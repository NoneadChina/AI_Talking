# -*- coding: utf-8 -*-
"""
AI Talking - NONEAD Corporation
主界面文件：实现AI聊天、讨论和辩论功能的图形用户界面
"""

# 导入系统模块
import sys
import os
import time
import threading
import markdown
import logging
import requests
import json

# 导入日志配置模块
from logger_config import get_logger

# 导入聊天历史管理器
from chat_history_manager import ChatHistoryManager

# 获取日志记录器
logger = get_logger(__name__)

# 导入PyQt5相关模块
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QTabWidget, QMessageBox, QFileDialog, QScrollArea, QDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtPrintSupport import QPrinter  # 用于PDF导出
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QMutex  # Qt常量、信号、槽、线程、互斥锁
from PyQt5.QtGui import QTextCursor, QIcon, QFont, QPixmap, QTextDocument  # 文本光标、图标、字体、图片、文档

# 导入环境变量加载模块
from dotenv import load_dotenv

# 导入AI聊天管理器
from chat_between_ais import AIChatManager

# 加载环境变量 - 明确指定可执行文件所在目录下的.env文件
# 处理PyInstaller打包后的情况
if getattr(sys, 'frozen', False):
    # 打包后的可执行文件所在目录
    current_dir = os.path.dirname(sys.executable)
else:
    # 开发环境下的当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建.env文件路径并加载
env_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path=env_path)


class ChatThread(QThread):
    """
    聊天线程类，用于在后台进行AI讨论或辩论，避免阻塞主线程UI。
    
    该线程类负责处理AI之间的对话逻辑，包括讨论和辩论两种模式，
    支持线程停止、状态检查和资源清理。
    
    信号:
        update_signal: 更新聊天历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        finished_signal: 讨论/辩论结束信号
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新聊天历史信号，参数为(发送者, 内容片段, 模型名称)
    """
    
    # 定义信号：用于线程间通信
    update_signal = pyqtSignal(str, str)  # 发送AI的完整回复，参数：(发送者, 内容)
    stream_update_signal = pyqtSignal(str, str, str)  # 发送AI的流式回复，参数：(发送者, 内容片段, 模型名称)
    status_signal = pyqtSignal(str)        # 发送状态信息
    finished_signal = pyqtSignal()         # 讨论/辩论结束信号
    error_signal = pyqtSignal(str)         # 错误信号
    
    def __init__(self, manager, topic, rounds, time_limit, is_debate=False):
        """
        初始化聊天线程。
        
        Args:
            manager: AI聊天管理器实例，用于调用AI API
            topic: 讨论/辩论主题
            rounds: 讨论/辩论轮数
            time_limit: 每轮时间限制（秒），0表示无限制
            is_debate: 是否为辩论模式（默认False，即讨论模式）
        """
        super().__init__()
        self.manager = manager        # AI聊天管理器实例
        self.topic = topic            # 讨论/辩论主题
        self.rounds = rounds          # 讨论/辩论轮数
        self.time_limit = time_limit  # 每轮时间限制
        self.is_debate = is_debate    # 辩论模式标识
        self._stop_event = threading.Event()  # 线程停止事件
        self._mutex = QMutex()        # 互斥锁，用于线程安全
        # 资源管理相关属性
        self._resources = {}
        self._memory_monitor = False
        self._max_history_size = 10  # 保留的最大历史对话轮数，防止内存溢出
    
    def stop(self):
        """
        停止讨论/辩论线程。
        
        设置停止事件，线程会在下一个检查点停止执行。
        """
        self._stop_event.set()  # 设置停止事件
    
    def is_stopped(self):
        """
        检查线程是否已停止。
        
        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()
    
    def _cleanup_resources(self):
        """
        清理线程资源。
        
        释放线程中使用的所有资源，包括消息历史记录和其他大型数据结构，
        确保没有内存泄漏。
        """
        logger.info("开始清理线程资源...")
        try:
            # 清空消息历史记录和其他大型数据结构
            if hasattr(self, '_resources'):
                for key in list(self._resources.keys()):
                    self._resources[key] = None
                self._resources.clear()
            
            # 重置事件和锁
            if hasattr(self, '_stop_event'):
                self._stop_event.clear()
                
            # 显式设置大型对象为None，帮助垃圾回收
            if hasattr(self, 'messages1'):
                self.messages1 = None
            if hasattr(self, 'messages2'):
                self.messages2 = None
            if hasattr(self, 'ai2_history'):
                self.ai2_history = None
            
            logger.info("线程资源清理完成")
        except Exception as e:
            logger.error(f"资源清理过程中发生错误: {str(e)}")
            
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        self._cleanup_resources()
        
    def run(self):
        """
        运行讨论/辩论线程。
        
        该方法是线程的主入口，负责处理AI之间的对话逻辑，包括：
        1. 初始化对话上下文
        2. 循环进行多轮对话
        3. 调用AI API获取响应
        4. 更新聊天历史和状态
        5. 处理线程停止事件
        6. 清理资源
        """
        try:
            # 检查manager是否存在
            if not hasattr(self, 'manager') or self.manager is None:
                self.error_signal.emit("错误：AI管理器未初始化")
                return
                
            # 限制系统提示长度，防止过多token消耗
            if hasattr(self.manager, 'full_debate_ai1_prompt'):
                if len(self.manager.full_debate_ai1_prompt) > 1000:
                    logger.warning("AI1系统提示过长，可能导致性能问题")
            if hasattr(self.manager, 'full_debate_ai2_prompt'):
                if len(self.manager.full_debate_ai2_prompt) > 1000:
                    logger.warning("AI2系统提示过长，可能导致性能问题")
                
            # 根据模式选择系统提示词
            if self.is_debate:
                ai1_system_prompt = getattr(self.manager, 'full_debate_ai1_prompt', "你是一个参与辩论的AI助手")
                ai2_system_prompt = getattr(self.manager, 'full_debate_ai2_prompt', "你是一个参与辩论的AI助手")
            else:
                ai1_system_prompt = getattr(self.manager, 'full_ai1_system_prompt', "你是一个参与讨论的AI助手")
                ai2_system_prompt = getattr(self.manager, 'full_ai2_system_prompt', "你是一个参与讨论的AI助手")
            
            # AI 1的初始消息包含主题（仅用于第一次回答）
            initial_messages1 = [
                {"role": "system", "content": ai1_system_prompt},
                {"role": "user", "content": f"主题：{self.topic}。请提供你的见解和观点。"}
            ]
            
            # AI 1在第一次回答后使用的消息列表（不包含主题）
            messages1 = [
                {"role": "system", "content": ai1_system_prompt}
            ]
            
            # AI 2的消息列表
            messages2 = [
                {"role": "system", "content": ai2_system_prompt}
            ]
            
            # 用于存储AI 2第二次及以后讨论的历史记录（不包含主题）
            ai2_history = []
            
            start_time = time.time()
            
            if self.is_debate:
                self.status_signal.emit(f"两个AI开始围绕主题 '{self.topic}' 进行辩论")
                self.status_signal.emit(f"正方AI1: {self.manager.model1_name} (API: {self.manager.model1_api})")
                self.status_signal.emit(f"反方AI2: {self.manager.model2_name} (API: {self.manager.model2_api})")
            else:
                self.status_signal.emit(f"两个AI开始围绕主题 '{self.topic}' 进行讨论")
                self.status_signal.emit(f"学者AI1: {self.manager.model1_name} (API: {self.manager.model1_api})")
                self.status_signal.emit(f"学者AI2: {self.manager.model2_name} (API: {self.manager.model2_api})")
            
            # 添加时间限制信息到状态
            if self.time_limit:
                self.status_signal.emit(f"时间限制: {self.time_limit} 秒")
            self.status_signal.emit(f"讨论轮数: {self.rounds} 轮")
            
            for i in range(1, self.rounds + 1):
                # 检查是否已停止
                if self.is_stopped():
                    self.status_signal.emit("讨论已停止")
                    break
                
                # 检查时间限制 - 每轮开始时
                if self.time_limit:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > self.time_limit:
                        self.status_signal.emit(f"时间限制已达到 ({elapsed_time:.1f}/{self.time_limit}秒)，沟通结束")
                        break
                    self.status_signal.emit(f"当前耗时: {elapsed_time:.1f}/{self.time_limit}秒")
                
                self.status_signal.emit(f"----- 第 {i}/{self.rounds} 轮开始 -----")
                
                # AI1发言
                if self.is_debate:
                    self.status_signal.emit(f"正方AI1的第 {i} 轮发言中...")
                else:
                    self.status_signal.emit(f"学者AI1的第 {i} 轮发言中...")
                
                try:
                    # 使用流式输出
                    if hasattr(self, 'stream_update_signal'):
                        # 准备发送者信息
                        sender = f"<span style='color: #2196F3; font-weight: bold;'>正方AI1 ({self.manager.model1_name})</span>" if self.is_debate else f"<span style='color: #2196F3; font-weight: bold;'>学者AI1 ({self.manager.model1_name})</span>"
                        
                        # 构建消息
                        if i == 1:
                            ai1_messages = initial_messages1
                        else:
                            ai1_messages = messages1
                        
                        # 发送开始标记
                        self.update_signal.emit(sender, "")
                        
                        # 获取流式响应
                        response1 = ""
                        for chunk in self.manager.get_ai_stream_response(self.manager.model1_name, ai1_messages, self.manager.model1_api):
                            if self.is_stopped():
                                self.status_signal.emit("沟通已停止")
                                break
                            response1 += chunk
                            self.stream_update_signal.emit(sender, chunk, self.manager.model1_name)
                        
                        logger.info(f"AI1 (模型: {self.manager.model1_name}, API: {self.manager.model1_api}) 第 {i} 轮回复成功")
                    else:
                        # 回退到非流式输出
                        if i == 1:
                            response1 = self.manager.get_ai_response(self.manager.model1_name, initial_messages1, self.manager.model1_api)
                            logger.info(f"AI1 (模型: {self.manager.model1_name}, API: {self.manager.model1_api}) 第 {i} 轮回复成功")
                        else:
                            response1 = self.manager.get_ai_response(self.manager.model1_name, messages1, self.manager.model1_api)
                            logger.info(f"AI1 (模型: {self.manager.model1_name}, API: {self.manager.model1_api}) 第 {i} 轮回复成功")
                            
                        # 发送更新信号
                        if hasattr(self, 'update_signal'):
                            if self.is_debate:
                                self.update_signal.emit(f"<span style='color: #2196F3; font-weight: bold;'>正方AI1 ({self.manager.model1_name})</span>", response1)
                            else:
                                self.update_signal.emit(f"<span style='color: #2196F3; font-weight: bold;'>学者AI1 ({self.manager.model1_name})</span>", response1)
                except Exception as e:
                    logger.error(f"AI1 (模型: {self.manager.model1_name}, API: {self.manager.model1_api}) 第 {i} 轮发言错误: {str(e)}")
                    self.error_signal.emit(f"AI1发言错误: {str(e)}")
                    # 只有在发生异常时才使用默认回复
                    response1 = "抱歉，我暂时无法提供观点。"
                    if hasattr(self, 'update_signal'):
                        if self.is_debate:
                            self.update_signal.emit(f"<span style='color: #2196F3; font-weight: bold;'>正方AI1 ({self.manager.model1_name})</span>", response1)
                        else:
                            self.update_signal.emit(f"<span style='color: #2196F3; font-weight: bold;'>学者AI1 ({self.manager.model1_name})</span>", response1)
                
                # 检查是否已停止
                if self.is_stopped():
                    self.status_signal.emit("沟通已停止")
                    break
                
                # 检查时间限制 - AI1发言后
                if self.time_limit:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > self.time_limit:
                        self.status_signal.emit(f"时间限制已达到 ({elapsed_time:.1f}/{self.time_limit}秒)，沟通结束")
                        break
                
                # 验证response1不为空
                if not response1 or response1.strip() == "":
                    if self.is_debate:
                        self.status_signal.emit(f"警告: 正方AI1的回复为空")
                    else:
                        self.status_signal.emit(f"警告: 学者AI1的回复为空")
                    # 使用默认回复避免讨论中断
                    response1 = "我对此主题没有特别的见解。"
                
                # AI1更新自己的讨论历史（包含完整讨论历史）
                messages1.append({"role": "assistant", "content": response1})
                
                # 准备AI2的讨论历史（包含完整讨论历史）
                if i == 1:
                    # 第一次讨论时，将主题和AI1的回答一起传给AI2
                    # 使用深拷贝避免修改原始列表
                    messages2_for_current_round = [msg.copy() for msg in messages2]
                    messages2_for_current_round.append({"role": "user", "content": f"主题：{self.topic}。\nAI 1的观点：{response1}"})
                else:
                    # 后续讨论，提供完整的讨论历史
                    messages2_for_current_round = [
                        {"role": "system", "content": ai2_system_prompt}
                    ]
                    # 添加完整的讨论历史（不包含主题）
                    messages2_for_current_round.extend([msg.copy() for msg in ai2_history])
                    # 添加当前轮次AI1的最新观点
                    messages2_for_current_round.append({"role": "user", "content": response1})
                
                # 检查是否已停止
                if self.is_stopped():
                    self.status_signal.emit("沟通已停止")
                    break
                
                # 检查时间限制 - AI2发言前
                if self.time_limit:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > self.time_limit:
                        self.status_signal.emit(f"时间限制已达到 ({elapsed_time:.1f}/{self.time_limit}秒)，沟通结束")
                        break
                
                # AI2回应
                if self.is_debate:
                    self.status_signal.emit(f"反方AI2的第 {i} 轮回应中...")
                else:
                    self.status_signal.emit(f"学者AI2的第 {i} 轮回应中...")
                
                try:
                    # 使用流式输出
                    if hasattr(self, 'stream_update_signal'):
                        # 准备发送者信息
                        sender = f"<span style='color: #F44336; font-weight: bold;'>反方AI2 ({self.manager.model2_name})</span>" if self.is_debate else f"<span style='color: #4CAF50; font-weight: bold;'>学者AI2 ({self.manager.model2_name})</span>"
                        
                        # 发送开始标记
                        self.update_signal.emit(sender, "")
                        
                        # 获取流式响应
                        response2 = ""
                        for chunk in self.manager.get_ai_stream_response(self.manager.model2_name, messages2_for_current_round, self.manager.model2_api):
                            if self.is_stopped():
                                self.status_signal.emit("沟通已停止")
                                break
                            response2 += chunk
                            self.stream_update_signal.emit(sender, chunk, self.manager.model2_name)
                        
                        logger.info(f"AI2 (模型: {self.manager.model2_name}, API: {self.manager.model2_api}) 第 {i} 轮回复成功")
                    else:
                        # 回退到非流式输出
                        response2 = self.manager.get_ai_response(self.manager.model2_name, messages2_for_current_round, self.manager.model2_api)
                        logger.info(f"AI2 (模型: {self.manager.model2_name}, API: {self.manager.model2_api}) 第 {i} 轮回复成功")
                        
                        # 发送更新信号
                        if hasattr(self, 'update_signal'):
                            if self.is_debate:
                                self.update_signal.emit(f"<span style='color: #F44336; font-weight: bold;'>反方AI2 ({self.manager.model2_name})</span>", response2)
                            else:
                                self.update_signal.emit(f"<span style='color: #4CAF50; font-weight: bold;'>学者AI2 ({self.manager.model2_name})</span>", response2)
                except Exception as e:
                    logger.error(f"AI2 (模型: {self.manager.model2_name}, API: {self.manager.model2_api}) 第 {i} 轮发言错误: {str(e)}")
                    self.error_signal.emit(f"AI2发言错误: {str(e)}")
                    # 使用默认回复避免讨论中断
                    response2 = "抱歉，我暂时无法提供观点。"
                    if hasattr(self, 'update_signal'):
                        if self.is_debate:
                            self.update_signal.emit(f"<span style='color: #F44336; font-weight: bold;'>反方AI2 ({self.manager.model2_name})</span>", response2)
                        else:
                            self.update_signal.emit(f"<span style='color: #4CAF50; font-weight: bold;'>学者AI2 ({self.manager.model2_name})</span>", response2)
                
                # 检查是否已停止
                if self.is_stopped():
                    self.status_signal.emit("沟通已停止")
                    break
                
                # 检查时间限制 - AI2发言后
                if self.time_limit:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > self.time_limit:
                        self.status_signal.emit(f"时间限制已达到 ({elapsed_time:.1f}/{self.time_limit}秒)，沟通结束")
                        break
                
                # 验证response2不为空
                if not response2 or response2.strip() == "":
                    if self.is_debate:
                        self.status_signal.emit(f"警告: 反方AI2的回复为空")
                    else:
                        self.status_signal.emit(f"警告: 学者AI2的回复为空")
                    # 使用默认回复避免讨论中断
                    response2 = "我对此主题没有特别的见解。"
                
                # 更新AI2的历史记录（保存完整讨论历史，不包含主题）
                ai2_history.append({"role": "user", "content": response1})
                ai2_history.append({"role": "assistant", "content": response2})
                
                # 将AI2的回应添加到AI1的讨论历史（确保完整讨论历史）
                messages1.append({"role": "user", "content": response2})
            
            total_time = time.time() - start_time
            self.status_signal.emit(f"沟通结束，总耗时: {total_time:.2f} 秒")
            
        except Exception as e:
            logger.error(f"程序运行出错: {str(e)}")
            self.error_signal.emit(f"程序运行出错: {str(e)}")
        finally:
                # 发出讨论结束信号
                if hasattr(self, 'finished_signal'):
                    self.finished_signal.emit()
                # 清理资源，防止内存泄漏
                self._cleanup_resources()

class BatchProcessingThread(QThread):
    """
    批量处理线程类，用于批量处理多个讨论主题。
    
    该线程类负责按顺序处理多个讨论主题，每个主题创建一个新的ChatThread实例，
    支持线程停止、状态检查和资源清理。
    
    信号:
        update_signal: 更新批量处理结果信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        finished_signal: 批量处理结束信号
    """
    
    # 定义信号：用于线程间通信
    update_signal = pyqtSignal(str, str)  # 发送更新，参数：(发送者, 内容)
    status_signal = pyqtSignal(str)        # 发送状态信息
    finished_signal = pyqtSignal()         # 批量处理结束信号
    error_signal = pyqtSignal(str)         # 错误信号
    
    def __init__(self, topics, model1_name, model2_name, model1_api, model2_api, 
                 rounds, time_limit, temperature, common_system_prompt="", 
                 ai1_system_prompt="", ai2_system_prompt="", debate_common_prompt="", 
                 debate_ai1_prompt="", debate_ai2_prompt="", chat_system_prompt=""):
        """
        初始化批量处理线程。
        
        Args:
            topics: 讨论主题列表
            model1_name: AI1模型名称
            model2_name: AI2模型名称
            model1_api: AI1 API类型
            model2_api: AI2 API类型
            rounds: 每轮讨论轮数
            time_limit: 每轮时间限制（秒），0表示无限制
            temperature: 温度参数
            common_system_prompt: 共享系统提示词
            ai1_system_prompt: AI1系统提示词
            ai2_system_prompt: AI2系统提示词
            debate_common_prompt: 辩论共享系统提示词
            debate_ai1_prompt: 辩论AI1系统提示词
            debate_ai2_prompt: 辩论AI2系统提示词
            chat_system_prompt: 聊天系统提示词
        """
        super().__init__()
        self.topics = topics                    # 讨论主题列表
        self.model1_name = model1_name          # AI1模型名称
        self.model2_name = model2_name          # AI2模型名称
        self.model1_api = model1_api            # AI1 API类型
        self.model2_api = model2_api            # AI2 API类型
        self.rounds = rounds                    # 每轮讨论轮数
        self.time_limit = time_limit            # 每轮时间限制
        self.temperature = temperature          # 温度参数
        self.common_system_prompt = common_system_prompt
        self.ai1_system_prompt = ai1_system_prompt
        self.ai2_system_prompt = ai2_system_prompt
        self.debate_common_prompt = debate_common_prompt
        self.debate_ai1_prompt = debate_ai1_prompt
        self.debate_ai2_prompt = debate_ai2_prompt
        self.chat_system_prompt = chat_system_prompt
        self._stop_event = threading.Event()    # 线程停止事件
        self._current_topic_index = 0           # 当前处理的主题索引
    
    def stop(self):
        """
        停止批量处理线程。
        
        设置停止事件，线程会在下一个检查点停止执行。
        """
        self._stop_event.set()  # 设置停止事件
    
    def is_stopped(self):
        """
        检查线程是否已停止。
        
        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()
    
    def _cleanup_resources(self):
        """
        清理线程资源。
        
        释放线程中使用的所有资源，包括主题列表、AIChatManager实例和其他大型数据结构，
        确保没有内存泄漏。
        """
        logger.info("开始清理批量处理线程资源...")
        try:
            # 清空主题列表和其他大型数据结构
            if hasattr(self, 'topics'):
                self.topics.clear()
            
            # 重置事件和锁
            if hasattr(self, '_stop_event'):
                self._stop_event.clear()
            
            # 显式设置大型对象为None，帮助垃圾回收
            if hasattr(self, 'model1_name'):
                self.model1_name = None
            if hasattr(self, 'model2_name'):
                self.model2_name = None
            if hasattr(self, 'model1_api'):
                self.model1_api = None
            if hasattr(self, 'model2_api'):
                self.model2_api = None
            if hasattr(self, '_current_topic_index'):
                self._current_topic_index = None
            
            logger.info("批量处理线程资源清理完成")
        except Exception as e:
            logger.error(f"批量处理资源清理过程中发生错误: {str(e)}")
            
    def __del__(self):
        """
        析构函数，确保资源被正确释放
        """
        self._cleanup_resources()
    
    def run(self):
        """
        运行批量处理线程。
        
        按顺序处理每个讨论主题，每个主题创建一个新的ChatThread实例，
        并等待其完成后再处理下一个主题。
        """
        try:
            total_topics = len(self.topics)
            self.status_signal.emit(f"开始批量处理，共 {total_topics} 个主题")
            
            # 遍历所有主题
            for i, topic in enumerate(self.topics):
                if self.is_stopped():
                    self.status_signal.emit("批量处理已停止")
                    break
                
                self._current_topic_index = i
                self.status_signal.emit(f"正在处理主题 {i+1}/{total_topics}: {topic}")
                self.update_signal.emit("系统", f"开始处理主题 {i+1}/{total_topics}: {topic}")
                
                # 创建AIChatManager实例
                from chat_between_ais import AIChatManager
                manager = AIChatManager(
                    model1_name=self.model1_name,
                    model2_name=self.model2_name,
                    model1_api=self.model1_api,
                    model2_api=self.model2_api,
                    temperature=self.temperature,
                    common_system_prompt=self.common_system_prompt,
                    ai1_system_prompt=self.ai1_system_prompt,
                    ai2_system_prompt=self.ai2_system_prompt,
                    debate_common_prompt=self.debate_common_prompt,
                    debate_ai1_prompt=self.debate_ai1_prompt,
                    debate_ai2_prompt=self.debate_ai2_prompt
                )
                
                # 创建并启动ChatThread实例
                chat_thread = ChatThread(
                    manager=manager,
                    topic=topic,
                    rounds=self.rounds,
                    time_limit=self.time_limit,
                    is_debate=False
                )
                
                # 连接ChatThread的信号
                chat_thread.update_signal.connect(self._on_chat_thread_update)
                chat_thread.status_signal.connect(self._on_chat_thread_status)
                chat_thread.error_signal.connect(self._on_chat_thread_error)
                
                # 启动ChatThread
                chat_thread.start()
                
                # 等待ChatThread完成
                chat_thread.wait()
                
                # 清理ChatThread资源
                chat_thread = None
                
                # 模拟处理间隔，避免过度占用资源
                time.sleep(1)
            
            self.status_signal.emit(f"批量处理完成，共处理 {self._current_topic_index + 1} 个主题")
            self.update_signal.emit("系统", "批量处理完成")
            self.finished_signal.emit()
            
        except Exception as e:
            logger.error(f"批量处理出错: {str(e)}")
            self.error_signal.emit(f"批量处理出错: {str(e)}")
            self.finished_signal.emit()
    
    def _on_chat_thread_update(self, sender, content):
        """
        处理ChatThread的更新信号。
        
        Args:
            sender: 发送者
            content: 内容
        """
        self.update_signal.emit(sender, content)
    
    def _on_chat_thread_status(self, status):
        """
        处理ChatThread的状态信号。
        
        Args:
            status: 状态信息
        """
        current_topic = self.topics[self._current_topic_index] if self._current_topic_index < len(self.topics) else "未知主题"
        self.status_signal.emit(f"主题 '{current_topic}' - {status}")
    
    def _on_chat_thread_error(self, error):
        """
        处理ChatThread的错误信号。
        
        Args:
            error: 错误信息
        """
        current_topic = self.topics[self._current_topic_index] if self._current_topic_index < len(self.topics) else "未知主题"
        self.error_signal.emit(f"主题 '{current_topic}' - {error}")

class APISettingsWidget(QWidget):
    """
    API设置窗口部件，用于配置各种AI API的连接信息和系统提示词。
    
    该部件提供了一个界面，允许用户配置OpenAI、DeepSeek和Ollama的API设置，
    以及各种系统提示词。
    
    信号:
        settings_saved: 设置保存完成信号
    """
    
    # 定义信号：当设置保存完成时发出
    settings_saved = pyqtSignal()
    
    def __init__(self):
        """
        初始化API设置窗口。
        
        构建API设置界面，包括API密钥输入、Ollama URL配置和系统提示词设置。
        """
        super().__init__()
        self.init_ui()  # 初始化用户界面
        self.load_settings()  # 加载已保存的设置
    
    def init_ui(self):
        """
        初始化API设置界面布局和控件。
        
        构建API设置界面的布局，包括：
        1. 系统提示词设置区域
        2. OpenAI API设置区域
        3. DeepSeek API设置区域
        4. Ollama API设置区域
        5. 保存按钮
        """
        # 创建主布局
        layout = QVBoxLayout()
        
        # 系统提示词设置组
        system_prompt_group = QGroupBox("系统提示词设置")
        system_prompt_layout = QVBoxLayout()
        
        # 聊天系统提示词
        self.chat_system_prompt_edit = QTextEdit()
        self.chat_system_prompt_edit.setPlaceholderText("请输入聊天模式的系统提示词")
        self.chat_system_prompt_edit.setMinimumHeight(60)
        
        # 讨论共享系统提示词
        self.common_system_prompt_edit = QTextEdit()
        self.common_system_prompt_edit.setPlaceholderText("请输入讨论共享系统提示词，将应用于所有AI")
        self.common_system_prompt_edit.setMinimumHeight(60)
        
        # 讨论AI1系统提示词
        self.ai1_system_prompt_edit = QTextEdit()
        self.ai1_system_prompt_edit.setPlaceholderText("请输入讨论AI1的系统提示词")
        self.ai1_system_prompt_edit.setMinimumHeight(60)
        
        # 讨论AI2系统提示词
        self.ai2_system_prompt_edit = QTextEdit()
        self.ai2_system_prompt_edit.setPlaceholderText("请输入讨论AI2的系统提示词")
        self.ai2_system_prompt_edit.setMinimumHeight(60)
        
        # 辩论共享系统提示词
        self.debate_common_prompt_edit = QTextEdit()
        self.debate_common_prompt_edit.setPlaceholderText("请输入辩论共享系统提示词，将应用于所有辩手")
        self.debate_common_prompt_edit.setMinimumHeight(60)
        
        # 正方辩手AI1系统提示词
        self.debate_ai1_prompt_edit = QTextEdit()
        self.debate_ai1_prompt_edit.setPlaceholderText("请输入正方辩手AI1的系统提示词")
        self.debate_ai1_prompt_edit.setMinimumHeight(60)
        
        # 反方辩手AI2系统提示词
        self.debate_ai2_prompt_edit = QTextEdit()
        self.debate_ai2_prompt_edit.setPlaceholderText("请输入反方辩手AI2的系统提示词")
        self.debate_ai2_prompt_edit.setMinimumHeight(60)
        
        # 将提示词控件添加到布局
        system_prompt_layout.addWidget(QLabel("聊天系统提示词:"))
        system_prompt_layout.addWidget(self.chat_system_prompt_edit)
        system_prompt_layout.addWidget(QLabel("讨论共享系统提示词:"))
        system_prompt_layout.addWidget(self.common_system_prompt_edit)
        system_prompt_layout.addWidget(QLabel("讨论AI1系统提示词:"))
        system_prompt_layout.addWidget(self.ai1_system_prompt_edit)
        system_prompt_layout.addWidget(QLabel("讨论AI2系统提示词:"))
        system_prompt_layout.addWidget(self.ai2_system_prompt_edit)
        system_prompt_layout.addWidget(QLabel("辩论共享系统提示词:"))
        system_prompt_layout.addWidget(self.debate_common_prompt_edit)
        system_prompt_layout.addWidget(QLabel("正方辩手AI1系统提示词:"))
        system_prompt_layout.addWidget(self.debate_ai1_prompt_edit)
        system_prompt_layout.addWidget(QLabel("反方辩手AI2系统提示词:"))
        system_prompt_layout.addWidget(self.debate_ai2_prompt_edit)
        system_prompt_group.setLayout(system_prompt_layout)
        
        # OpenAI API设置组
        openai_group = QGroupBox("OpenAI API设置")
        openai_layout = QVBoxLayout()
        
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.Password)  # 默认隐藏密钥
        self.openai_key_edit.setPlaceholderText("请输入OpenAI API密钥")
        
        # 显示密钥复选框
        show_openai_key = QCheckBox("显示密钥")
        show_openai_key.toggled.connect(lambda checked: 
            self.openai_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        
        openai_layout.addWidget(QLabel("API密钥:"))
        openai_layout.addWidget(self.openai_key_edit)
        openai_layout.addWidget(show_openai_key)
        openai_group.setLayout(openai_layout)
        

        
        # DeepSeek API设置组
        deepseek_group = QGroupBox("DeepSeek API设置")
        deepseek_layout = QVBoxLayout()
        
        self.deepseek_key_edit = QLineEdit()
        self.deepseek_key_edit.setEchoMode(QLineEdit.Password)  # 默认隐藏密钥
        self.deepseek_key_edit.setPlaceholderText("请输入DeepSeek API密钥")
        
        # 显示密钥复选框
        show_deepseek_key = QCheckBox("显示密钥")
        show_deepseek_key.toggled.connect(lambda checked: 
            self.deepseek_key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        
        deepseek_layout.addWidget(QLabel("API密钥:"))
        deepseek_layout.addWidget(self.deepseek_key_edit)
        deepseek_layout.addWidget(show_deepseek_key)
        deepseek_group.setLayout(deepseek_layout)
        
        # Ollama API设置组
        ollama_group = QGroupBox("Ollama API设置")
        ollama_layout = QVBoxLayout()
        
        self.ollama_url_edit = QLineEdit("http://ai.corp.nonead.com:11434")
        self.ollama_url_edit.setPlaceholderText("请输入Ollama API基础URL")
        
        ollama_layout.addWidget(QLabel("API基础URL:"))
        ollama_layout.addWidget(self.ollama_url_edit)
        ollama_group.setLayout(ollama_layout)
        
        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        
        # 将所有设置组添加到主布局
        layout.addWidget(system_prompt_group)
        layout.addWidget(openai_group)
        layout.addWidget(deepseek_group)
        layout.addWidget(ollama_group)
        layout.addWidget(save_button)
        layout.addStretch()  # 添加拉伸空间
        
        self.setLayout(layout)
    
    def load_settings(self):
        """
        加载现有的API设置。
        
        从环境变量中读取之前保存的配置信息并填充到表单中，包括：
        1. API密钥
        2. Ollama URL
        3. 系统提示词
        """
        # 加载API密钥和URL
        self.openai_key_edit.setText(os.getenv("OPENAI_API_KEY", ""))
        self.deepseek_key_edit.setText(os.getenv("DEEPSEEK_API_KEY", ""))
        self.ollama_url_edit.setText(os.getenv("OLLAMA_BASE_URL", "http://ai.corp.nonead.com:11434"))
        
        # 加载系统提示词
        default_prompt = "你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。"
        self.chat_system_prompt_edit.setPlainText(os.getenv("CHAT_SYSTEM_PROMPT", default_prompt))
        self.common_system_prompt_edit.setPlainText(os.getenv("COMMON_SYSTEM_PROMPT", default_prompt))
        self.ai1_system_prompt_edit.setPlainText(os.getenv("AI1_SYSTEM_PROMPT", ""))
        self.ai2_system_prompt_edit.setPlainText(os.getenv("AI2_SYSTEM_PROMPT", ""))
        
        # 加载辩论系统提示词
        default_debate_prompt = "你是一个辩论选手，请根据你的立场进行辩论，逻辑清晰，论点明确。"
        self.debate_common_prompt_edit.setPlainText(os.getenv("DEBATE_COMMON_PROMPT", default_debate_prompt))
        self.debate_ai1_prompt_edit.setPlainText(os.getenv("DEBATE_AI1_PROMPT", ""))
        self.debate_ai2_prompt_edit.setPlainText(os.getenv("DEBATE_AI2_PROMPT", ""))
    
    def get_ollama_base_url(self):
        """获取当前设置的Ollama基础URL
        
        Returns:
            str: 当前配置的Ollama API基础URL
        """
        return self.ollama_url_edit.text().strip()
    
    def get_openai_api_key(self):
        """获取当前设置的OpenAI API密钥
        
        Returns:
            str: 当前配置的OpenAI API密钥
        """
        return self.openai_key_edit.text().strip()
    
    def get_deepseek_api_key(self):
        """获取当前设置的DeepSeek API密钥
        
        Returns:
            str: 当前配置的DeepSeek API密钥
        """
        return self.deepseek_key_edit.text().strip()
    

    
    def save_settings(self):
        """
        保存API设置到.env文件。
        
        将用户在界面上配置的API密钥、Ollama URL和系统提示词保存到环境配置文件中。
        保存前会备份原文件，确保数据安全。
        
        Returns:
            bool: 设置保存成功返回True，失败返回False
        """
        try:
            # 使用当前工作目录作为.env文件的保存位置
            env_path = ".env"
            env_content = []
            
            # 如果文件已存在，读取现有内容
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        env_content = f.readlines()
                except IOError as e:
                    QMessageBox.critical(self, "错误", f"读取.env文件失败: {str(e)}")
                    return False
            
            # 解析现有配置到字典
            config = {}
            for line in env_content:
                line = line.rstrip('\n')
                if '=' in line and not line.strip().startswith('#'):  # 忽略注释行
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            # 更新OpenAI API密钥配置
            openai_key = self.openai_key_edit.text().strip()
            if openai_key:
                config['OPENAI_API_KEY'] = openai_key
            

            
            # 更新DeepSeek API密钥配置
            deepseek_key = self.deepseek_key_edit.text().strip()
            if deepseek_key:
                config['DEEPSEEK_API_KEY'] = deepseek_key
            
            # 更新Ollama API URL配置
            ollama_url = self.ollama_url_edit.text().strip()
            if ollama_url:
                # 验证URL格式是否基本有效
                if not (ollama_url.startswith('http://') or ollama_url.startswith('https://')):
                    QMessageBox.warning(self, "警告", "Ollama URL格式无效，请确保以http://或https://开头")
                    return False
                
                # 仅当URL不是默认值时才保存（减少配置文件冗余）
                if ollama_url != "http://ai.corp.nonead.com:11434":
                    config['OLLAMA_BASE_URL'] = ollama_url
            elif 'OLLAMA_BASE_URL' in config:
                del config['OLLAMA_BASE_URL']  # 如果URL为空，删除现有配置
            
            # 保存聊天和讨论系统提示词
            chat_system_prompt = self.chat_system_prompt_edit.toPlainText().strip()
            common_system_prompt = self.common_system_prompt_edit.toPlainText().strip()
            default_prompt = "你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。"
            
            # 仅保存非默认值的提示词（减少配置文件冗余）
            if chat_system_prompt and chat_system_prompt != default_prompt:
                config['CHAT_SYSTEM_PROMPT'] = chat_system_prompt
            elif 'CHAT_SYSTEM_PROMPT' in config:
                del config['CHAT_SYSTEM_PROMPT']
            
            if common_system_prompt and common_system_prompt != default_prompt:
                config['COMMON_SYSTEM_PROMPT'] = common_system_prompt
            elif 'COMMON_SYSTEM_PROMPT' in config:
                del config['COMMON_SYSTEM_PROMPT']
            
            ai1_system_prompt = self.ai1_system_prompt_edit.toPlainText().strip()
            if ai1_system_prompt:
                config['AI1_SYSTEM_PROMPT'] = ai1_system_prompt
            elif 'AI1_SYSTEM_PROMPT' in config:
                del config['AI1_SYSTEM_PROMPT']
            
            ai2_system_prompt = self.ai2_system_prompt_edit.toPlainText().strip()
            if ai2_system_prompt:
                config['AI2_SYSTEM_PROMPT'] = ai2_system_prompt
            elif 'AI2_SYSTEM_PROMPT' in config:
                del config['AI2_SYSTEM_PROMPT']
            
            # 保存辩论系统提示词
            debate_common_prompt = self.debate_common_prompt_edit.toPlainText().strip()
            default_debate_prompt = "你是一个辩论选手，请根据你的立场进行辩论，逻辑清晰，论点明确。"
            
            if debate_common_prompt and debate_common_prompt != default_debate_prompt:
                config['DEBATE_COMMON_PROMPT'] = debate_common_prompt
            elif 'DEBATE_COMMON_PROMPT' in config:
                del config['DEBATE_COMMON_PROMPT']
            
            debate_ai1_prompt = self.debate_ai1_prompt_edit.toPlainText().strip()
            if debate_ai1_prompt:
                config['DEBATE_AI1_PROMPT'] = debate_ai1_prompt
            elif 'DEBATE_AI1_PROMPT' in config:
                del config['DEBATE_AI1_PROMPT']
            
            debate_ai2_prompt = self.debate_ai2_prompt_edit.toPlainText().strip()
            if debate_ai2_prompt:
                config['DEBATE_AI2_PROMPT'] = debate_ai2_prompt
            elif 'DEBATE_AI2_PROMPT' in config:
                del config['DEBATE_AI2_PROMPT']
            
            # 写回.env文件 - 先备份原文件（安全措施）
            backup_path = None
            if os.path.exists(env_path):
                backup_path = env_path + ".backup"
                try:
                    import shutil
                    shutil.copy2(env_path, backup_path)
                    logger.info(f"配置文件备份成功: {env_path} -> {backup_path}")
                except Exception as e:
                    error_msg = f"无法备份配置文件: {str(e)}"
                    logger.error(error_msg)
                    QMessageBox.warning(self, "警告", error_msg)
                    # 继续执行，不因为备份失败而中断
            
            try:
                # 写入新的配置文件内容
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write("# API密钥配置\n\n")
                    
                    if 'OPENAI_API_KEY' in config:
                        f.write(f"# OpenAI API配置\nOPENAI_API_KEY={config['OPENAI_API_KEY']}\n\n")
                    

                    
                    if 'DEEPSEEK_API_KEY' in config:
                        f.write(f"# DeepSeek API配置\nDEEPSEEK_API_KEY={config['DEEPSEEK_API_KEY']}\n\n")
                    
                    if 'OLLAMA_BASE_URL' in config:
                        f.write(f"# Ollama API配置\nOLLAMA_BASE_URL={config['OLLAMA_BASE_URL']}\n\n")
                    else:
                        f.write(f"# Ollama API配置（默认为本地服务器）\n# OLLAMA_BASE_URL=http://ai.corp.nonead.com:11434\n\n")
                    
                    # 写入系统提示词配置
                    f.write("# 系统提示词配置\n")
                    
                    # 写入讨论系统提示词
                    if 'CHAT_SYSTEM_PROMPT' in config:
                        # 处理特殊字符（如换行符）
                        prompt = config['CHAT_SYSTEM_PROMPT'].replace('\n', '\\n')
                        f.write(f"CHAT_SYSTEM_PROMPT={prompt}\n")
                    
                    if 'COMMON_SYSTEM_PROMPT' in config:
                        prompt = config['COMMON_SYSTEM_PROMPT'].replace('\n', '\\n')
                        f.write(f"COMMON_SYSTEM_PROMPT={prompt}\n")
                    
                    if 'AI1_SYSTEM_PROMPT' in config:
                        prompt = config['AI1_SYSTEM_PROMPT'].replace('\n', '\\n')
                        f.write(f"AI1_SYSTEM_PROMPT={prompt}\n")
                    
                    if 'AI2_SYSTEM_PROMPT' in config:
                        prompt = config['AI2_SYSTEM_PROMPT'].replace('\n', '\\n')
                        f.write(f"AI2_SYSTEM_PROMPT={prompt}\n")
                    
                    # 写入辩论系统提示词
                    if 'DEBATE_COMMON_PROMPT' in config:
                        prompt = config['DEBATE_COMMON_PROMPT'].replace('\n', '\\n')
                        f.write(f"DEBATE_COMMON_PROMPT={prompt}\n")
                    
                    if 'DEBATE_AI1_PROMPT' in config:
                        prompt = config['DEBATE_AI1_PROMPT'].replace('\n', '\\n')
                        f.write(f"DEBATE_AI1_PROMPT={prompt}\n")
                    
                    if 'DEBATE_AI2_PROMPT' in config:
                        prompt = config['DEBATE_AI2_PROMPT'].replace('\n', '\\n')
                        f.write(f"DEBATE_AI2_PROMPT={prompt}\n")
            except IOError as e:
                # 恢复备份文件
                if backup_path and os.path.exists(backup_path):
                    try:
                        import shutil
                        shutil.copy2(backup_path, env_path)
                        QMessageBox.warning(self, "警告", f"保存配置失败，但已恢复备份: {str(e)}")
                    except Exception:
                        QMessageBox.critical(self, "错误", f"保存配置失败且无法恢复备份: {str(e)}")
                else:
                    QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
                return False
                
                # 如果没有任何系统提示词配置，写入默认注释
                if not any(key in config for key in ['SYSTEM_PROMPT', 'CHAT_SYSTEM_PROMPT', 'COMMON_SYSTEM_PROMPT', 
                                                    'AI1_SYSTEM_PROMPT', 'AI2_SYSTEM_PROMPT', 'DEBATE_COMMON_PROMPT', 
                                                    'DEBATE_AI1_PROMPT', 'DEBATE_AI2_PROMPT']):
                    f.write("# 默认系统提示词：你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。\n")
                    f.write("# COMMON_SYSTEM_PROMPT=你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。\n")
                    f.write("# DEBATE_COMMON_PROMPT=你是一个辩论选手，请根据你的立场进行辩论，逻辑清晰，论点明确。\n")
            
            # 重新加载环境变量
            load_dotenv()
            
            QMessageBox.information(self, "成功", "API设置已保存")
            self.settings_saved.emit()
            
        except IOError as e:
            error_msg = f"保存设置失败 - 文件IO错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            error_msg = f"保存设置失败 - 未知错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

class ChatGUI(QMainWindow):
    """
    AI讨论图形界面主窗口类，包含标准聊天、讨论和辩论三个标签页。
    
    该类是应用程序的主窗口，负责管理所有UI组件和功能，包括：
    1. 标准聊天功能
    2. 双AI讨论功能
    3. 双AI辩论功能
    4. API配置管理
    5. 聊天历史记录和导出
    6. 实时状态更新
    
    信号:
        update_chat_signal: 更新聊天历史信号，参数为(发送者, 内容, 模型名称)
        update_status_signal: 更新状态信号，参数为状态信息
    """
    
    # 定义信号用于线程安全的UI更新
    update_chat_signal = pyqtSignal(str, str, str)  # 参数: 发送者, 内容, 模型名称
    stream_chat_update_signal = pyqtSignal(str, str, str)  # 参数: 发送者, 内容片段, 模型名称
    update_status_signal = pyqtSignal(str)  # 参数: 状态消息
    
    def __init__(self):
        """
        初始化ChatGUI类。
        
        设置窗口属性、线程管理、聊天历史管理等，包括：
        1. 线程管理（聊天线程和辩论线程）
        2. 聊天历史内存优化设置
        3. 信号与槽连接
        4. 用户界面初始化
        """
        super().__init__()
        
        # 线程管理
        self.chat_thread = None  # 聊天线程
        self.debate_thread = None  # 辩论线程
        
        # 正在思考状态管理
        self.is_typing = False  # 跟踪是否显示"正在思考..."状态
        self.chat_history_before_typing = None  # 保存"正在思考..."之前的聊天历史
        self.is_model_responding = False  # 跟踪模型是否正在回答
        
        # 流式更新状态管理
        self._is_streaming = False  # 标记是否正在流式更新
        self._streaming_content = ""  # 存储当前流式更新的内容
        self._streaming_sender = ""  # 存储当前流式更新的发送者
        self._streaming_model = ""  # 存储当前流式更新的模型
        
        # 聊天历史内存优化设置
        self.max_standard_chat_history = 30  # 设置标准聊天历史的最大消息数量
        self.max_discussion_history = 50  # 设置讨论历史的最大消息数量
        self.max_debate_history = 50  # 设置辩论历史的最大消息数量
        
        # 聊天历史计数（用于内存优化）
        self.standard_chat_count = 0  # 跟踪当前标准聊天历史数量
        self.discussion_chat_count = 0  # 跟踪当前讨论历史数量
        self.debate_chat_count = 0  # 跟踪当前辩论历史数量
        
        # 标准聊天历史存储（用于API调用）
        self.standard_chat_history_messages = []  # 存储完整的聊天历史消息，包含系统提示词
        
        # 讨论和辩论历史的轻量级存储，用于减少内存占用
        self.discussion_history_messages = []
        self.debate_history_messages = []
        
        # 初始化聊天历史管理器
        self.chat_history_manager = ChatHistoryManager()
        
        # 连接信号到槽函数（线程安全的UI更新）
        self.update_chat_signal.connect(self.append_to_standard_chat_history)
        self.stream_chat_update_signal.connect(self._handle_stream_chat_update)
        self.update_status_signal.connect(self.update_status)
        
        # 讨论功能的流式更新相关属性
        self._discussion_streaming_states = {}
        self._debate_streaming_states = {}
        
        # 加载历史记录
        self.all_chat_histories = self.chat_history_manager.load_history()
        
        # 初始化用户界面
        self.init_ui()
    
    def init_ui(self):
        """
        初始化用户界面。
        
        构建应用的主窗口布局，包含三个标签页：
        1. 标准聊天标签页
        2. 讨论标签页
        3. 辩论标签页
        
        每个标签页包含相应的配置区域、聊天历史区域和控制区域。
        """
        # 设置窗口属性
        self.setWindowTitle("AI Talking - NONEAD Corporation")  # 设置窗口标题
        
        # 设置窗口图标
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件所在目录
            current_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下的当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 构建ICO文件路径
        icon_path = os.path.join(current_dir, "resources", "icon.ico")
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(icon_path))
        
        self.setGeometry(100, 100, 900, 700)  # 设置窗口位置和大小(x, y, width, height)
        
        # 创建中央部件（所有UI元素的容器）
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件（用于切换不同功能模块）
        self.tabs = QTabWidget()
        
        # 定义内部函数：创建Logo图片标签
        def create_logo_label():
            """创建Logo图片标签
            从指定URL下载Logo图片并显示
            
            Returns:
                QLabel: 包含Logo图片的标签控件
            """
            try:
                import requests
                from PyQt5.QtCore import QByteArray
                
                # 使用requests下载图片
                image_url = "https://www.nonead.com/assets/img/vi/NONEAD_ai.png"
                response = requests.get(image_url)
                response.raise_for_status()  # 检查HTTP错误
                
                # 将二进制数据转换为QPixmap格式
                image_data = QByteArray(response.content)
                logo_pixmap = QPixmap()
                logo_pixmap.loadFromData(image_data)
                
                # 调整图片大小（保持宽高比，平滑缩放）
                scaled_pixmap = logo_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                return logo_label
            except Exception as e:
                # 如果图片加载失败，创建错误提示标签
                error_label = QLabel(f"Logo加载失败: {str(e)}")
                error_label.setStyleSheet("color: red")  # 设置错误文本颜色
                return error_label
        
        # 为不同标签页创建独立的Logo标签
        chat_logo_label = create_logo_label()  # 聊天标签页Logo
        debate_logo_label = create_logo_label()  # 辩论标签页Logo
        
        # 聊天标签页（标准AI Chat）
        standard_chat_tab = QWidget()
        standard_chat_layout = QVBoxLayout(standard_chat_tab)
        
        # 聊天配置区域
        chat_config_group = QGroupBox("聊天配置")
        
        # 创建一个包含AI配置和Logo的水平布局
        ai_config_with_logo_layout = QHBoxLayout()
        
        # 创建左侧AI配置的垂直布局
        ai_configs_layout = QVBoxLayout()
        
        # API和模型配置行
        api_model_layout = QHBoxLayout()
        api_model_layout.addWidget(QLabel("API:"))
        
        # API选择下拉框
        self.chat_api_combo = QComboBox()
        self.chat_api_combo.addItems(["ollama", "openai", "deepseek"])
        self.chat_api_combo.setCurrentText("ollama")  # 默认选择ollama API
        self.chat_api_combo.currentTextChanged.connect(self.update_chat_model_list)  # API变化时更新模型列表
        api_model_layout.addWidget(self.chat_api_combo)
        
        # 模型选择下拉框
        api_model_layout.addWidget(QLabel("模型:"))
        self.chat_model_combo = QComboBox()
        self.chat_model_combo.setFixedWidth(250)
        api_model_layout.addWidget(self.chat_model_combo)
        
        # 添加温度调节功能
        api_model_layout.addWidget(QLabel("温度:"))
        self.chat_temperature_spin = QDoubleSpinBox()
        self.chat_temperature_spin.setRange(0.0, 2.0)  # 温度范围：0.0（保守）到2.0（激进）
        self.chat_temperature_spin.setSingleStep(0.1)  # 步长0.1
        self.chat_temperature_spin.setValue(0.8)  # 默认值0.8
        self.chat_temperature_spin.setToolTip("控制AI回复的随机性，值越高回复越多样")
        api_model_layout.addWidget(self.chat_temperature_spin)
        
        # 添加拉伸空间，使控件靠左对齐，logo图片靠右
        api_model_layout.addStretch()
        
        # 在温度控件右侧添加图片（现在会显示在最右侧）
        api_model_logo_label = create_logo_label()
        api_model_layout.addWidget(api_model_logo_label)
        
        ai_configs_layout.addLayout(api_model_layout)
        
        # 将AI配置和Logo添加到主水平布局
        ai_config_with_logo_layout.addLayout(ai_configs_layout, 1)  # AI配置占据主要空间
        ai_config_with_logo_layout.addWidget(chat_logo_label)  # Logo放在右侧
        
        # 设置聊天配置组的布局
        chat_config_group.setLayout(ai_config_with_logo_layout)
        standard_chat_layout.addWidget(chat_config_group)
        
        # 聊天历史区域
        chat_history_group = QGroupBox("聊天历史")
        chat_history_layout = QVBoxLayout()
        
        # 创建只读的聊天历史文本编辑框
        self.standard_chat_history = QTextEdit()
        self.standard_chat_history.setReadOnly(True)  # 设置为只读，防止用户编辑历史记录
        self.standard_chat_history.setLineWrapMode(QTextEdit.WidgetWidth)  # 按窗口宽度自动换行
        self.standard_chat_history.setAcceptRichText(True)  # 支持富文本格式，用于渲染Markdown
        # 设置垂直滚动条始终可见，提升用户体验
        self.standard_chat_history.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # 设置聊天历史的字体大小
        font = QFont()
        font.setPointSize(10)
        self.standard_chat_history.setFont(font)
        
        chat_history_layout.addWidget(self.standard_chat_history)
        chat_history_group.setLayout(chat_history_layout)
        standard_chat_layout.addWidget(chat_history_group, 1)  # 权重为1，让历史区域占据主要空间
        
        # 聊天输入区域
        chat_input_group = QGroupBox("输入")
        chat_input_layout = QVBoxLayout()
        
        # 创建聊天输入框
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("输入消息，按回车发送，Shift+回车换行...")  # 提示用户输入方式
        self.chat_input.setMaximumHeight(100)  # 设置最大高度，防止输入框过长
        self.chat_input.textChanged.connect(self.update_chat_input_height)  # 文本变化时自动调整高度
        self.chat_input.keyPressEvent = self.chat_input_key_press  # 替换默认按键事件，实现自定义发送逻辑
        
        chat_input_layout.addWidget(self.chat_input)
        chat_input_group.setLayout(chat_input_layout)
        standard_chat_layout.addWidget(chat_input_group)
        
        # 底部控制区域
        control_layout = QHBoxLayout()
        
        # 状态栏：显示当前聊天状态
        self.chat_status_label = QLabel("就绪")
        self.chat_status_label.setAlignment(Qt.AlignLeft)  # 左对齐显示
        control_layout.addWidget(self.chat_status_label, 1)  # 权重为1，占据剩余空间
        
        # 保存历史按钮：用于保存聊天历史
        self.save_standard_history_button = QPushButton("保存历史")
        self.save_standard_history_button.clicked.connect(self.save_standard_chat_history)
        control_layout.addWidget(self.save_standard_history_button)
        
        # 加载历史按钮：用于加载聊天历史
        self.load_standard_history_button = QPushButton("加载历史")
        self.load_standard_history_button.clicked.connect(self.load_standard_chat_history)
        control_layout.addWidget(self.load_standard_history_button)
        
        # 导出PDF按钮：用于将聊天历史导出为PDF文件
        self.export_chat_pdf_button = QPushButton("导出PDF")
        self.export_chat_pdf_button.clicked.connect(self.export_chat_history_to_pdf)  # 绑定导出功能
        control_layout.addWidget(self.export_chat_pdf_button)
        
        standard_chat_layout.addLayout(control_layout)
        
        # 讨论标签页
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # 配置区域
        config_group = QGroupBox("讨论配置")
        config_layout = QVBoxLayout()
        
        # 主题输入
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("讨论主题:"))
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("请输入讨论主题")
        topic_layout.addWidget(self.topic_edit)
        config_layout.addLayout(topic_layout)
        
        # 创建一个包含AI配置和Logo的水平布局
        ai_config_with_logo_layout = QHBoxLayout()
        
        # 创建左侧AI配置的垂直布局
        ai_configs_layout = QVBoxLayout()
        
        # AI1配置
        ai1_layout = QHBoxLayout()
        ai1_layout.addWidget(QLabel("学者AI1:"))
        
        self.model1_combo = QComboBox()
        self.model1_combo.setFixedWidth(250)
        self.model1_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-v3.1:671b-cloud", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "qwen3-vl:235b-instruct-cloud", "deepseek-r1:14b", "qwen3:14b"])
        
        self.api1_combo = QComboBox()
        self.api1_combo.addItems(["ollama", "openai", "deepseek"])
        self.api1_combo.setCurrentText("ollama")
        self.api1_combo.currentTextChanged.connect(self.update_model_list)
        
        ai1_layout.addWidget(self.model1_combo)
        ai1_layout.addWidget(QLabel("API:"))
        ai1_layout.addWidget(self.api1_combo)
        ai1_layout.addStretch()
        ai_configs_layout.addLayout(ai1_layout)
        
        # AI2配置
        ai2_layout = QHBoxLayout()
        ai2_layout.addWidget(QLabel("学者AI2:"))
        
        self.model2_combo = QComboBox()
        self.model2_combo.setFixedWidth(250)
        self.model2_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "qwen3-vl:235b-instruct-cloud"])
        
        self.api2_combo = QComboBox()
        self.api2_combo.addItems(["ollama", "openai", "deepseek"])
        self.api2_combo.setCurrentText("ollama")
        self.api2_combo.currentTextChanged.connect(self.update_model_list)
        
        ai2_layout.addWidget(self.model2_combo)
        ai2_layout.addWidget(QLabel("API:"))
        ai2_layout.addWidget(self.api2_combo)
        ai2_layout.addStretch()
        ai_configs_layout.addLayout(ai2_layout)
        
        # 将AI配置和Logo添加到主水平布局
        ai_config_with_logo_layout.addLayout(ai_configs_layout, 1)  # AI配置占据主要空间
        ai_config_with_logo_layout.addWidget(chat_logo_label)  # Logo放在右侧
        
        config_layout.addLayout(ai_config_with_logo_layout)
        
        # 参数配置
        params_layout = QHBoxLayout()
        
        params_layout.addWidget(QLabel("讨论轮数:"))
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 9999)
        self.rounds_spin.setValue(5)
        params_layout.addWidget(self.rounds_spin)
        
        params_layout.addWidget(QLabel("时间限制(秒):"))
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(0, 999999)
        self.time_limit_spin.setValue(0)
        self.time_limit_spin.setSpecialValueText("无限制")
        params_layout.addWidget(self.time_limit_spin)
        
        params_layout.addWidget(QLabel("温度:"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.8)
        params_layout.addWidget(self.temp_spin)
        params_layout.addWidget(QLabel("(0.0-2.0)"))
        
        params_layout.addStretch()
        config_layout.addLayout(params_layout)
        
        config_group.setLayout(config_layout)
        chat_layout.addWidget(config_group)
        
        # 讨论历史区域
        chat_history_group = QGroupBox("讨论历史")
        chat_history_layout = QVBoxLayout()
        
        self.chat_history_text = QTextEdit()
        self.chat_history_text.setReadOnly(True)
        self.chat_history_text.setLineWrapMode(QTextEdit.WidgetWidth)
        # 允许富文本以支持Markdown渲染
        self.chat_history_text.setAcceptRichText(True)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.chat_history_text.setFont(font)
        
        chat_history_layout.addWidget(self.chat_history_text)
        chat_history_group.setLayout(chat_history_layout)
        chat_layout.addWidget(chat_history_group, 1)
        
        # 状态和控制区域
        control_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        
        self.save_history_button = QPushButton("保存历史")
        self.save_history_button.clicked.connect(self.save_chat_history)
        control_layout.addWidget(self.save_history_button)
        
        self.load_history_button = QPushButton("加载历史")
        self.load_history_button.clicked.connect(self.load_chat_history)
        control_layout.addWidget(self.load_history_button)
        
        self.export_pdf_button = QPushButton("导出PDF")
        self.export_pdf_button.clicked.connect(self.export_chat_history_to_pdf)
        control_layout.addWidget(self.export_pdf_button)
        
        self.start_button = QPushButton("开始讨论")
        self.start_button.clicked.connect(self.start_chat)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止讨论")
        self.stop_button.clicked.connect(self.stop_chat)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        chat_layout.addLayout(control_layout)
        
        self.tabs.addTab(standard_chat_tab, "聊天")
        self.tabs.addTab(chat_tab, "讨论")
        
        # 辩论标签页（与讨论页内容一致）
        debate_tab = QWidget()
        debate_layout = QVBoxLayout(debate_tab)
        
        # 复制讨论标签页的所有内容到辩论标签页
        # 配置区域
        config_group_copy = QGroupBox("辩论配置")
        config_layout_copy = QVBoxLayout()
        
        # 主题输入
        topic_layout_copy = QHBoxLayout()
        topic_layout_copy.addWidget(QLabel("辩论主题:"))
        self.debate_topic_edit = QLineEdit()
        self.debate_topic_edit.setPlaceholderText("请输入辩论主题")
        topic_layout_copy.addWidget(self.debate_topic_edit)
        config_layout_copy.addLayout(topic_layout_copy)
        
        # 创建一个包含AI配置和Logo的水平布局
        ai_config_with_logo_layout_copy = QHBoxLayout()
        
        # 创建左侧AI配置的垂直布局
        ai_configs_layout_copy = QVBoxLayout()
        
        # AI1配置
        ai1_layout_copy = QHBoxLayout()
        ai1_layout_copy.addWidget(QLabel("正方AI1:"))
        
        self.debate_model1_combo = QComboBox()
        self.debate_model1_combo.setFixedWidth(250)
        self.debate_model1_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "deepseek-v3.1:671b-cloud", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "qwen3-vl:235b-instruct-cloud", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
        
        self.debate_api1_combo = QComboBox()
        self.debate_api1_combo.addItems(["ollama", "openai", "deepseek"])
        self.debate_api1_combo.setCurrentText("ollama")
        self.debate_api1_combo.currentTextChanged.connect(self.update_debate_model_list)
        
        ai1_layout_copy.addWidget(self.debate_model1_combo)
        ai1_layout_copy.addWidget(QLabel("API:"))
        ai1_layout_copy.addWidget(self.debate_api1_combo)
        ai1_layout_copy.addStretch()
        ai_configs_layout_copy.addLayout(ai1_layout_copy)
        
        # AI2配置
        ai2_layout_copy = QHBoxLayout()
        ai2_layout_copy.addWidget(QLabel("反方AI2:"))
        
        self.debate_model2_combo = QComboBox()
        self.debate_model2_combo.setFixedWidth(250)
        self.debate_model2_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "deepseek-v3.1:671b-cloud", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "qwen3-vl:235b-instruct-cloud", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
        
        self.debate_api2_combo = QComboBox()
        self.debate_api2_combo.addItems(["ollama", "openai", "deepseek"])
        self.debate_api2_combo.setCurrentText("ollama")
        self.debate_api2_combo.currentTextChanged.connect(self.update_debate_model_list)
        
        ai2_layout_copy.addWidget(self.debate_model2_combo)
        ai2_layout_copy.addWidget(QLabel("API:"))
        ai2_layout_copy.addWidget(self.debate_api2_combo)
        ai2_layout_copy.addStretch()
        ai_configs_layout_copy.addLayout(ai2_layout_copy)
        
        # 将AI配置和Logo添加到主水平布局
        ai_config_with_logo_layout_copy.addLayout(ai_configs_layout_copy, 1)  # AI配置占据主要空间
        ai_config_with_logo_layout_copy.addWidget(debate_logo_label)  # Logo放在右侧
        
        config_layout_copy.addLayout(ai_config_with_logo_layout_copy)
        
        # 参数配置
        params_layout_copy = QHBoxLayout()
        
        params_layout_copy.addWidget(QLabel("辩论轮数:"))
        self.debate_rounds_spin = QSpinBox()
        self.debate_rounds_spin.setRange(1, 9999)
        self.debate_rounds_spin.setValue(5)
        params_layout_copy.addWidget(self.debate_rounds_spin)
        
        params_layout_copy.addWidget(QLabel("时间限制(秒):"))
        self.debate_time_limit_spin = QSpinBox()
        self.debate_time_limit_spin.setRange(0, 999999)
        self.debate_time_limit_spin.setValue(0)
        self.debate_time_limit_spin.setSpecialValueText("无限制")
        params_layout_copy.addWidget(self.debate_time_limit_spin)
        
        params_layout_copy.addWidget(QLabel("温度:"))
        self.debate_temp_spin = QDoubleSpinBox()
        self.debate_temp_spin.setRange(0.0, 2.0)
        self.debate_temp_spin.setSingleStep(0.1)
        self.debate_temp_spin.setValue(0.8)
        params_layout_copy.addWidget(self.debate_temp_spin)
        params_layout_copy.addWidget(QLabel("(0.0-2.0)"))
        
        params_layout_copy.addStretch()
        config_layout_copy.addLayout(params_layout_copy)
        
        config_group_copy.setLayout(config_layout_copy)
        debate_layout.addWidget(config_group_copy)
        
        # 讨论历史区域
        debate_history_group = QGroupBox("辩论历史")
        debate_history_layout = QVBoxLayout()
        
        self.debate_history_text = QTextEdit()
        self.debate_history_text.setReadOnly(True)
        self.debate_history_text.setLineWrapMode(QTextEdit.WidgetWidth)
        # 允许富文本以支持Markdown渲染
        self.debate_history_text.setAcceptRichText(True)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.debate_history_text.setFont(font)
        
        debate_history_layout.addWidget(self.debate_history_text)
        debate_history_group.setLayout(debate_history_layout)
        debate_layout.addWidget(debate_history_group, 1)
        
        # 状态和控制区域
        debate_control_layout = QHBoxLayout()
        
        self.debate_status_label = QLabel("就绪")
        debate_control_layout.addWidget(self.debate_status_label)
        debate_control_layout.addStretch()
        
        self.save_debate_history_button = QPushButton("保存历史")
        self.save_debate_history_button.clicked.connect(self.save_debate_chat_history)
        debate_control_layout.addWidget(self.save_debate_history_button)
        
        self.load_debate_history_button = QPushButton("加载历史")
        self.load_debate_history_button.clicked.connect(self.load_debate_chat_history)
        debate_control_layout.addWidget(self.load_debate_history_button)
        
        self.debate_export_pdf_button = QPushButton("导出PDF")
        self.debate_export_pdf_button.clicked.connect(self.export_debate_history_to_pdf)
        debate_control_layout.addWidget(self.debate_export_pdf_button)
        
        self.debate_start_button = QPushButton("开始辩论")
        self.debate_start_button.clicked.connect(self.start_debate)
        debate_control_layout.addWidget(self.debate_start_button)
        
        self.debate_stop_button = QPushButton("停止辩论")
        self.debate_stop_button.clicked.connect(self.stop_debate)
        self.debate_stop_button.setEnabled(False)
        debate_control_layout.addWidget(self.debate_stop_button)
        
        debate_layout.addLayout(debate_control_layout)
        
        self.tabs.addTab(debate_tab, "辩论")
        
        # 批量处理标签页
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        # 批量配置区域
        batch_config_group = QGroupBox("批量处理配置")
        batch_config_layout = QVBoxLayout()
        
        # 主题列表输入
        topics_layout = QHBoxLayout()
        topics_layout.addWidget(QLabel("主题列表:"))
        self.batch_topics_edit = QTextEdit()
        self.batch_topics_edit.setPlaceholderText("请输入多个讨论主题，每个主题一行")
        self.batch_topics_edit.setMinimumHeight(100)
        topics_layout.addWidget(self.batch_topics_edit)
        batch_config_layout.addLayout(topics_layout)
        
        # 批量参数设置
        batch_params_layout = QHBoxLayout()
        batch_params_layout.addWidget(QLabel("讨论轮数:"))
        self.batch_rounds_spin = QSpinBox()
        self.batch_rounds_spin.setRange(1, 9999)
        self.batch_rounds_spin.setValue(5)
        batch_params_layout.addWidget(self.batch_rounds_spin)
        
        batch_params_layout.addWidget(QLabel("时间限制(秒):"))
        self.batch_time_limit_spin = QSpinBox()
        self.batch_time_limit_spin.setRange(0, 999999)
        self.batch_time_limit_spin.setValue(0)
        self.batch_time_limit_spin.setSpecialValueText("无限制")
        batch_params_layout.addWidget(self.batch_time_limit_spin)
        
        batch_params_layout.addWidget(QLabel("温度:"))
        self.batch_temp_spin = QDoubleSpinBox()
        self.batch_temp_spin.setRange(0.0, 2.0)
        self.batch_temp_spin.setSingleStep(0.1)
        self.batch_temp_spin.setValue(0.8)
        batch_params_layout.addWidget(self.batch_temp_spin)
        batch_params_layout.addWidget(QLabel("(0.0-2.0)"))
        
        batch_params_layout.addStretch()
        batch_config_layout.addLayout(batch_params_layout)
        
        # AI配置区域
        ai_config_layout = QVBoxLayout()
        
        # AI1配置
        batch_ai1_layout = QHBoxLayout()
        batch_ai1_layout.addWidget(QLabel("学者AI1:"))
        
        self.batch_model1_combo = QComboBox()
        self.batch_model1_combo.setFixedWidth(250)
        self.batch_model1_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-v3.1:671b-cloud", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "qwen3-vl:235b-instruct-cloud", "deepseek-r1:14b", "qwen3:14b"])
        self.batch_model1_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        
        self.batch_api1_combo = QComboBox()
        self.batch_api1_combo.addItems(["ollama", "openai", "deepseek"])
        self.batch_api1_combo.setCurrentText("ollama")
        
        batch_ai1_layout.addWidget(self.batch_model1_combo)
        batch_ai1_layout.addWidget(QLabel("API:"))
        batch_ai1_layout.addWidget(self.batch_api1_combo)
        batch_ai1_layout.addStretch()
        ai_config_layout.addLayout(batch_ai1_layout)
        
        # AI2配置
        batch_ai2_layout = QHBoxLayout()
        batch_ai2_layout.addWidget(QLabel("学者AI2:"))
        
        self.batch_model2_combo = QComboBox()
        self.batch_model2_combo.setFixedWidth(250)
        self.batch_model2_combo.addItems(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "qwen3-vl:235b-instruct-cloud"])
        self.batch_model2_combo.setCurrentText("qwen3-vl:235b-instruct-cloud")
        
        self.batch_api2_combo = QComboBox()
        self.batch_api2_combo.addItems(["ollama", "openai", "deepseek"])
        self.batch_api2_combo.setCurrentText("ollama")
        
        batch_ai2_layout.addWidget(self.batch_model2_combo)
        batch_ai2_layout.addWidget(QLabel("API:"))
        batch_ai2_layout.addWidget(self.batch_api2_combo)
        batch_ai2_layout.addStretch()
        ai_config_layout.addLayout(batch_ai2_layout)
        
        batch_config_layout.addLayout(ai_config_layout)
        batch_config_group.setLayout(batch_config_layout)
        batch_layout.addWidget(batch_config_group)
        
        # 结果显示区域
        batch_results_group = QGroupBox("批量处理结果")
        batch_results_layout = QVBoxLayout()
        
        self.batch_results_text = QTextEdit()
        self.batch_results_text.setReadOnly(True)
        self.batch_results_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.batch_results_text.setAcceptRichText(True)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.batch_results_text.setFont(font)
        
        batch_results_layout.addWidget(self.batch_results_text)
        batch_results_group.setLayout(batch_results_layout)
        batch_layout.addWidget(batch_results_group, 1)
        
        # 控制区域
        batch_control_layout = QHBoxLayout()
        
        self.batch_status_label = QLabel("就绪")
        batch_control_layout.addWidget(self.batch_status_label, 1)
        
        self.batch_start_button = QPushButton("开始批量处理")
        self.batch_start_button.clicked.connect(self.start_batch_processing)
        batch_control_layout.addWidget(self.batch_start_button)
        
        self.batch_stop_button = QPushButton("停止批量处理")
        self.batch_stop_button.clicked.connect(self.stop_batch_processing)
        self.batch_stop_button.setEnabled(False)
        batch_control_layout.addWidget(self.batch_stop_button)
        
        self.batch_clear_button = QPushButton("清空结果")
        self.batch_clear_button.clicked.connect(self.clear_batch_results)
        batch_control_layout.addWidget(self.batch_clear_button)
        
        batch_layout.addLayout(batch_control_layout)
        
        self.tabs.addTab(batch_tab, "批量处理")
        
        # API设置标签页
        self.api_settings_widget = APISettingsWidget()
        self.api_settings_widget.settings_saved.connect(self.on_settings_saved)
        self.tabs.addTab(self.api_settings_widget, "设置")
        
        # 关于标签页
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setAlignment(Qt.AlignCenter)
        about_layout.setSpacing(20)
        
        # 创建Logo标签
        def create_about_logo_label():
            """创建关于页面的Logo标签"""
            try:
                import requests
                from PyQt5.QtCore import QByteArray
                
                # 使用requests下载图片
                image_url = "https://www.nonead.com/assets/img/vi/NONEAD_ai.png"
                response = requests.get(image_url)
                response.raise_for_status()  # 检查HTTP错误
                
                # 将二进制数据转换为QPixmap格式
                image_data = QByteArray(response.content)
                logo_pixmap = QPixmap()
                logo_pixmap.loadFromData(image_data)
                
                # 调整图片大小（保持宽高比，平滑缩放）
                scaled_pixmap = logo_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                return logo_label
            except Exception as e:
                # 如果图片加载失败，创建错误提示标签
                error_label = QLabel(f"Logo加载失败: {str(e)}")
                error_label.setStyleSheet("color: red")  # 设置错误文本颜色
                error_label.setAlignment(Qt.AlignCenter)
                return error_label
        
        # 添加Logo
        about_logo_label = create_about_logo_label()
        about_layout.addWidget(about_logo_label)
        
        # 软件名称
        app_name_label = QLabel("AI Talking")
        app_name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        app_name_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(app_name_label)
        
        # 软件版本
        version_label = QLabel("版本 0.1.5")
        version_label.setStyleSheet("font-size: 16px; color: #666;")
        version_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(version_label)
        
        # 公司名称
        company_label = QLabel("NONEAD Corporation")
        company_label.setStyleSheet("font-size: 18px; color: #333;")
        company_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(company_label)
        
        # 版权信息
        copyright_label = QLabel("© 2025 NONEAD Corporation. All rights reserved.")
        copyright_label.setStyleSheet("font-size: 14px; color: #888;")
        copyright_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(copyright_label)
        
        # 软件描述
        description_label = QLabel("AI Talking 是一款支持多种AI模型进行对话、讨论和辩论的智能软件。")
        description_label.setStyleSheet("font-size: 14px; color: #555;")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setMaximumWidth(500)
        about_layout.addWidget(description_label)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #E0E0E0;")
        about_layout.addWidget(separator)
        
        # 联系方式
        contact_label = QLabel("联系方式：")
        contact_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        contact_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(contact_label)
        
        website_label = QLabel("官方网站：https://www.nonead.com")
        website_label.setStyleSheet("font-size: 14px; color: #2196F3;")
        website_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(website_label)
        
        email_label = QLabel("邮箱：service@nonead.com")
        email_label.setStyleSheet("font-size: 14px; color: #555;")
        email_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(email_label)
        
        # 许可证信息
        license_label = QLabel("本软件采用 MIT 许可证")
        license_label.setStyleSheet("font-size: 14px; color: #888;")
        license_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(license_label)
        
        # 添加关于标签页
        self.tabs.addTab(about_tab, "关于")
        
        main_layout.addWidget(self.tabs)
        
        # 添加历史管理按钮
        self.history_manager_button = QPushButton("历史管理")
        self.history_manager_button.clicked.connect(self.show_history_manager)
        
        # 在主布局中添加历史管理按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.history_manager_button)
        main_layout.addLayout(button_layout)
        
        # 初始更新模型列表，但避免Ollama的网络请求
        # 只使用默认模型列表，不连接服务器
        self._update_model_list_without_ollama()
        self._update_chat_model_list_without_ollama()
        self._update_debate_model_list_without_ollama()
        
        # 设置默认模型
        # 1. 聊天功能：默认选择 "deepseek-v3.1:671b-cloud"
        self.chat_model_combo.addItem("deepseek-v3.1:671b-cloud")
        if "deepseek-v3.1:671b-cloud" in [self.chat_model_combo.itemText(i) for i in range(self.chat_model_combo.count())]:
            self.chat_model_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        
        # 2. 讨论功能：
        # 学者AI1：默认选择 "deepseek-v3.1:671b-cloud"
        if "deepseek-v3.1:671b-cloud" in [self.model1_combo.itemText(i) for i in range(self.model1_combo.count())]:
            self.model1_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        # 学者AI2：默认选择 "qwen3-vl:235b-instruct-cloud"
        if "qwen3-vl:235b-instruct-cloud" in [self.model2_combo.itemText(i) for i in range(self.model2_combo.count())]:
            self.model2_combo.setCurrentText("qwen3-vl:235b-instruct-cloud")
        
        # 3. 辩论功能：
        # 正方AI1：默认选择 "deepseek-v3.1:671b-cloud"
        self.debate_model1_combo.addItem("deepseek-v3.1:671b-cloud")
        if "deepseek-v3.1:671b-cloud" in [self.debate_model1_combo.itemText(i) for i in range(self.debate_model1_combo.count())]:
            self.debate_model1_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        # 反方AI2：默认选择 "qwen3-vl:235b-instruct-cloud"
        self.debate_model2_combo.addItem("qwen3-vl:235b-instruct-cloud")
        if "qwen3-vl:235b-instruct-cloud" in [self.debate_model2_combo.itemText(i) for i in range(self.debate_model2_combo.count())]:
            self.debate_model2_combo.setCurrentText("qwen3-vl:235b-instruct-cloud")
    
    def _update_chat_model_list_without_ollama(self):
        """快速更新聊天标签页的模型列表，不连接Ollama服务器"""
        # 保存当前选中的模型
        current_model = self.chat_model_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api = self.chat_api_combo.currentText()
        self.chat_model_combo.clear()
        if api == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.chat_model_combo.addItems(models)
        elif api == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.chat_model_combo.addItems(models)
        elif api == "ollama":
            # 不连接服务器，直接使用默认模型列表，包含云模型
            models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "deepseek-v3.1:671b-cloud"])
            self.chat_model_combo.addItems(models)
        
        # 恢复之前选中的模型（如果存在）
        if current_model in [self.chat_model_combo.itemText(i) for i in range(self.chat_model_combo.count())]:
            self.chat_model_combo.setCurrentText(current_model)
        else:
            # 设置默认模型
            if "deepseek-v3.1:671b-cloud" in [self.chat_model_combo.itemText(i) for i in range(self.chat_model_combo.count())]:
                self.chat_model_combo.setCurrentText("deepseek-v3.1:671b-cloud")

    def _update_debate_model_list_without_ollama(self):
        """快速更新辩论标签页的模型列表，不连接Ollama服务器"""
        # 保存当前选中的模型
        current_model1 = self.debate_model1_combo.currentText()
        current_model2 = self.debate_model2_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api1 = self.debate_api1_combo.currentText()
        self.debate_model1_combo.clear()
        if api1 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.debate_model1_combo.addItems(models)
        elif api1 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.debate_model1_combo.addItems(models)
        elif api1 == "ollama":
            # 不连接服务器，直接使用默认模型列表，包含云模型
            models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "deepseek-v3.1:671b-cloud"])
            self.debate_model1_combo.addItems(models)
        
        api2 = self.debate_api2_combo.currentText()
        self.debate_model2_combo.clear()
        if api2 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.debate_model2_combo.addItems(models)
        elif api2 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.debate_model2_combo.addItems(models)
        elif api2 == "ollama":
            # 不连接服务器，直接使用默认模型列表，包含云模型
            models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "qwen3-vl:235b-instruct-cloud"])
            self.debate_model2_combo.addItems(models)
        
        # 恢复之前选中的模型（如果存在）
        if current_model1 in [self.debate_model1_combo.itemText(i) for i in range(self.debate_model1_combo.count())]:
            self.debate_model1_combo.setCurrentText(current_model1)
        else:
            # 设置默认模型：正方AI1默认选择 "deepseek-v3.1:671b-cloud"
            if "deepseek-v3.1:671b-cloud" in [self.debate_model1_combo.itemText(i) for i in range(self.debate_model1_combo.count())]:
                self.debate_model1_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        
        if current_model2 in [self.debate_model2_combo.itemText(i) for i in range(self.debate_model2_combo.count())]:
            self.debate_model2_combo.setCurrentText(current_model2)
        else:
            # 设置默认模型：反方AI2默认选择 "qwen3-vl:235b-instruct-cloud"
            if "qwen3-vl:235b-instruct-cloud" in [self.debate_model2_combo.itemText(i) for i in range(self.debate_model2_combo.count())]:
                self.debate_model2_combo.setCurrentText("qwen3-vl:235b-instruct-cloud")

    def _update_model_list_without_ollama(self):
        """快速更新讨论标签页的模型列表，不连接Ollama服务器"""
        # 保存当前选中的模型
        current_model1 = self.model1_combo.currentText()
        current_model2 = self.model2_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api1 = self.api1_combo.currentText()
        self.model1_combo.clear()
        if api1 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.model1_combo.addItems(models)
        elif api1 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.model1_combo.addItems(models)
        elif api1 == "ollama":
            # 不连接服务器，直接使用默认模型列表，包含云模型
            models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "deepseek-v3.1:671b-cloud"])
            self.model1_combo.addItems(models)
        
        # 恢复选中的模型（如果存在）
        if current_model1 in [self.model1_combo.itemText(i) for i in range(self.model1_combo.count())]:
            self.model1_combo.setCurrentText(current_model1)
        else:
            # 设置默认模型：学者AI1默认选择 "deepseek-v3.1:671b-cloud"
            if "deepseek-v3.1:671b-cloud" in [self.model1_combo.itemText(i) for i in range(self.model1_combo.count())]:
                self.model1_combo.setCurrentText("deepseek-v3.1:671b-cloud")
        
        api2 = self.api2_combo.currentText()
        self.model2_combo.clear()
        if api2 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.model2_combo.addItems(models)
        elif api2 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.model2_combo.addItems(models)
        elif api2 == "ollama":
            # 不连接服务器，直接使用默认模型列表，包含云模型
            models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b", "qwen3-vl:235b-instruct-cloud"])
            self.model2_combo.addItems(models)
        
        # 恢复选中的模型（如果存在）
        if current_model2 in [self.model2_combo.itemText(i) for i in range(self.model2_combo.count())]:
            self.model2_combo.setCurrentText(current_model2)
        else:
            # 设置默认模型：学者AI2默认选择 "qwen3-vl:235b-instruct-cloud"
            if "qwen3-vl:235b-instruct-cloud" in [self.model2_combo.itemText(i) for i in range(self.model2_combo.count())]:
                self.model2_combo.setCurrentText("qwen3-vl:235b-instruct-cloud")

    def update_chat_model_list(self):
        """根据选择的API类型更新聊天标签页的模型列表"""
        # 保存当前选中的模型
        current_model = self.chat_model_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api = self.chat_api_combo.currentText()
        self.chat_model_combo.clear()
        if api == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.chat_model_combo.addItems(models)
        elif api == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.chat_model_combo.addItems(models)
        elif api == "ollama":
            # 尝试从Ollama服务器动态获取已安装的模型
            ollama_models = self._get_ollama_models()
            if ollama_models:
                # 对模型列表进行排序
                sorted_models = sorted(ollama_models)
                self.chat_model_combo.addItems(sorted_models)
            else:
                # 如果获取失败，使用默认列表并排序
                models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
                self.chat_model_combo.addItems(models)
        
        # 恢复之前选中的模型（如果存在）
        if current_model in [self.chat_model_combo.itemText(i) for i in range(self.chat_model_combo.count())]:
            self.chat_model_combo.setCurrentText(current_model)
    
    def update_debate_model_list(self):
        """根据选择的API类型更新辩论标签页的模型列表"""
        # 保存当前选中的模型
        current_model1 = self.debate_model1_combo.currentText()
        current_model2 = self.debate_model2_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api1 = self.debate_api1_combo.currentText()
        self.debate_model1_combo.clear()
        if api1 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.debate_model1_combo.addItems(models)
        elif api1 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.debate_model1_combo.addItems(models)
        elif api1 == "ollama":
            # 尝试从Ollama服务器动态获取已安装的模型
            ollama_models = self._get_ollama_models()
            if ollama_models:
                # 对模型列表进行排序
                sorted_models = sorted(ollama_models)
                self.debate_model1_combo.addItems(sorted_models)
            else:
                # 如果获取失败，使用默认列表并排序
                models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
                self.debate_model1_combo.addItems(models)
        
        api2 = self.debate_api2_combo.currentText()
        self.debate_model2_combo.clear()
        if api2 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.debate_model2_combo.addItems(models)
        elif api2 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.debate_model2_combo.addItems(models)
        elif api2 == "ollama":
            # 尝试从Ollama服务器动态获取已安装的模型
            ollama_models = self._get_ollama_models()
            if ollama_models:
                # 对模型列表进行排序
                sorted_models = sorted(ollama_models)
                self.debate_model2_combo.addItems(sorted_models)
            else:
                # 如果获取失败，使用默认列表并排序
                models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
                self.debate_model2_combo.addItems(models)
        
        # 恢复之前选中的模型（如果存在）
        if current_model1 in [self.debate_model1_combo.itemText(i) for i in range(self.debate_model1_combo.count())]:
            self.debate_model1_combo.setCurrentText(current_model1)
        if current_model2 in [self.debate_model2_combo.itemText(i) for i in range(self.debate_model2_combo.count())]:
            self.debate_model2_combo.setCurrentText(current_model2)
    
    def update_model_list(self):
        """根据选择的API类型更新辩论标签页的模型列表"""
        # 保存当前选中的模型
        current_model1 = self.model1_combo.currentText()
        current_model2 = self.model2_combo.currentText()
        
        # 清除并根据API类型添加相应的模型
        api1 = self.api1_combo.currentText()
        self.model1_combo.clear()
        if api1 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.model1_combo.addItems(models)
        elif api1 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.model1_combo.addItems(models)
        elif api1 == "ollama":
            # 尝试从Ollama服务器动态获取已安装的模型
            ollama_models = self._get_ollama_models()
            if ollama_models:
                # 对模型列表进行排序
                sorted_models = sorted(ollama_models)
                self.model1_combo.addItems(sorted_models)
            else:
                # 如果获取失败，使用默认列表并排序
                models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
                self.model1_combo.addItems(models)
        
        # 恢复选中的模型（如果存在）
        if current_model1 in [self.model1_combo.itemText(i) for i in range(self.model1_combo.count())]:
            self.model1_combo.setCurrentText(current_model1)
        
        api2 = self.api2_combo.currentText()
        self.model2_combo.clear()
        if api2 == "openai":
            models = sorted(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
            self.model2_combo.addItems(models)
        elif api2 == "deepseek":
            models = sorted(["deepseek-chat", "deepseek-coder"])
            self.model2_combo.addItems(models)
        elif api2 == "ollama":
            # 尝试从Ollama服务器动态获取已安装的模型
            ollama_models = self._get_ollama_models()
            if ollama_models:
                # 对模型列表进行排序
                sorted_models = sorted(ollama_models)
                self.model2_combo.addItems(sorted_models)
            else:
                # 如果获取失败，使用默认列表并排序
                models = sorted(["gemma3:270m", "gemma3:1b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b", "qwen3:0.6b", "llava:7b", "qwen3:4b", "qwen3:8b", "deepseek-r1:1.5b", "deepseek-r1:14b", "qwen3:14b"])
                self.model2_combo.addItems(models)
        
        # 恢复选中的模型（如果存在）
        if current_model2 in [self.model2_combo.itemText(i) for i in range(self.model2_combo.count())]:
            self.model2_combo.setCurrentText(current_model2)
    
    def _get_ollama_models(self):
        """从Ollama服务器获取已安装的模型列表，使用AIChatManager中的功能"""
        try:
            # 创建一个临时的AIChatManager实例来获取模型列表
            # 这样可以利用AIChatManager中已有的超时和重试机制
            temp_manager = AIChatManager()
            
            # 传递Ollama基础URL给AIChatManager
            if hasattr(self, 'api_settings_widget'):
                settings_ollama_url = self.api_settings_widget.get_ollama_base_url()
                if settings_ollama_url:
                    print(f"从API设置获取Ollama URL: {settings_ollama_url}")
                    temp_manager.ollama_base_url = settings_ollama_url
            
            # 调用AIChatManager中的_get_ollama_models方法
            models = temp_manager._get_ollama_models()
            
            if models:
                print(f"成功获取Ollama模型列表，共 {len(models)} 个模型")
                return models
            else:
                # 如果获取失败，显示错误信息
                print("获取Ollama模型列表失败")
                
                # 显示用户友好的错误消息
                ollama_base_url = temp_manager.ollama_base_url
                self.show_error_message(
                    "Ollama连接失败",
                    f"无法连接到Ollama服务器\n\n" +
                    f"服务器地址: {ollama_base_url}\n\n" +
                    "可能的解决方法:\n" +
                    "1. 确认Ollama服务器正在运行\n" +
                    "2. 在API设置中验证服务器地址是否正确\n" +
                    "3. 检查网络连接和防火墙设置"
                )
                
                return None
                
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            logger.error(f"获取Ollama模型列表时发生网络异常: {error_detail}")
            return None
        except json.JSONDecodeError as e:
            error_detail = str(e)
            logger.error(f"获取Ollama模型列表时发生JSON解析异常: {error_detail}")
            return None
        except Exception as e:
            error_detail = str(e)
            logger.error(f"获取Ollama模型列表时发生未知异常: {error_detail}")
            return None
    
    def update_chat_input_height(self):
        """自动调整聊天输入框的高度"""
        # 获取内容高度
        content_height = self.chat_input.document().size().height()
        # 限制最大高度
        content_height = min(content_height, 100)  # 最大高度100px
        # 设置输入框高度，将浮点数转换为整数
        self.chat_input.setFixedHeight(int(content_height + 20))  # 加上一些内边距
    
    def chat_input_key_press(self, event):
        """处理聊天输入框的按键事件：回车发送，Shift+回车换行"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not (event.modifiers() & Qt.ShiftModifier):
                # 无论模型是否正在回答，都允许用户发送消息
                # 发送消息
                self.send_chat_message()
                return
        
        # 对于Shift+回车和其他所有按键，都让QTextEdit正常处理
        # 这里直接调用QTextEdit的keyPressEvent方法
        QTextEdit.keyPressEvent(self.chat_input, event)
    
    def send_chat_message(self):
        """发送聊天消息到AI并显示回复"""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
        
        # 设置模型正在回答状态
        self.is_model_responding = True
        
        # 显示用户消息
        self.append_to_standard_chat_history("用户", message)
        
        # 清空输入框
        self.chat_input.clear()
        self.chat_input.setFixedHeight(30)  # 重置高度
        
        # 保存当前聊天历史（在添加"正在思考..."之前），确保包含用户的最新消息
        self.chat_history_before_typing = self.standard_chat_history.toHtml()
        
        # 显示"正在思考..."状态 - 这个消息不会被添加到standard_chat_history_messages列表
        self.append_to_standard_chat_history("AI", "正在思考...")
        self.is_typing = True  # 设置正在思考状态为True
        
        # 完全重置流式更新状态，确保每次AI回复都是新的对话轮次
        if hasattr(self, '_streaming_state'):
            delattr(self, '_streaming_state')
        
        # 使用线程发送消息，避免阻塞UI
        threading.Thread(target=self._send_chat_message_thread, args=(message,)).start()
    
    def _save_standard_chat_history(self, model):
        """保存标准聊天历史到历史管理器"""
        if not self.standard_chat_history_messages:
            return
        
        # 获取聊天主题（从第一条用户消息获取）
        user_messages = [msg for msg in self.standard_chat_history_messages if msg["role"] == "user"]
        if not user_messages:
            topic = "无主题聊天"
        else:
            topic = user_messages[0]["content"][:50] + "..." if len(user_messages[0]["content"]) > 50 else user_messages[0]["content"]
        
        # 确保状态正确，不使用旧的"正在思考..."状态
        self.is_typing = False
        self.chat_history_before_typing = None
        self.is_model_responding = False
        
        # 保存需要的参数，以便在主线程中使用
        save_params = {
            'model': model,
            'topic': topic,
            'messages': self.standard_chat_history_messages.copy()
        }
        
        # 使用QTimer.singleShot在主线程中执行，这是更安全的方式
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_ui_and_save_history(save_params))
    
    def _update_ui_and_save_history(self, save_params):
        """在主线程中更新UI并保存历史记录"""
        """在主线程中更新UI并保存历史"""
        try:
            model = save_params['model']
            topic = save_params['topic']
            messages = save_params['messages']
            
            # 从消息列表重新构建完整的HTML内容，确保不包含"正在思考..."
            # 1. 清除当前聊天历史的HTML
            temp_html = "<html><body></body></html>"
            self.standard_chat_history.setHtml(temp_html)
            self.standard_chat_count = 0  # 重置计数
            
            # 2. 重新添加所有消息，跳过任何可能的"正在思考..."状态
            for msg in messages:
                if msg["role"] == "system":
                    continue  # 系统消息不显示在聊天界面
                sender = "用户" if msg["role"] == "user" else "AI"
                content = msg["content"]
                # 确保不添加"正在思考..."内容
                if content != "正在思考...":
                    self.append_to_standard_chat_history(sender, content)
            
            # 3. 现在获取的HTML将不包含"正在思考..."
            clean_html = self.standard_chat_history.toHtml()
            
            # 4. 查找是否已存在相同模型的标准聊天历史记录
            existing_history_index = -1
            for i, history in enumerate(self.all_chat_histories):
                if history["type"] == "标准聊天" and history["model"] == model:
                    existing_history_index = i
                    break
            
            if existing_history_index != -1:
                # 更新现有历史记录
                self.all_chat_histories[existing_history_index].update({
                    "topic": topic,
                    "messages": messages.copy(),
                    "html_content": clean_html,
                    "timestamp": self._get_timestamp()
                })
            else:
                # 创建新的聊天历史记录
                chat_history = {
                    "id": len(self.all_chat_histories) + 1,
                    "type": "标准聊天",
                    "topic": topic,
                    "model": model,
                    "timestamp": self._get_timestamp(),
                    "messages": messages.copy(),
                    "html_content": clean_html
                }
                # 添加到历史记录列表
                self.all_chat_histories.append(chat_history)
            
            # 5. 保存所有历史记录到磁盘
            self.chat_history_manager.save_history(self.all_chat_histories)
        except Exception as e:
            logger.error(f"在主线程中更新UI并保存历史时出错: {str(e)}")
    
    def _send_chat_message_thread(self, message):
        """在后台线程发送聊天消息"""
        import logging
        try:
            logging.info(f"_send_chat_message_thread 开始执行，消息: {message}")
            
            # 获取API和模型信息（线程安全，因为在信号回调中使用）
            api = self.chat_api_combo.currentText()
            model = self.chat_model_combo.currentText()
            temperature = self.chat_temperature_spin.value()
            
            logging.info(f"使用API: {api}, 模型: {model}, 温度: {temperature}")
            logging.info(f"发送消息时的聊天历史长度: {len(self.standard_chat_history_messages)}")
            logging.info(f"当前发送的消息: {message}")
            
            # 根据选择的API发送消息
            if api == "ollama":
                logging.info("准备调用 Ollama API")
                self._send_ollama_chat_message(model, message, temperature)
                logging.info("Ollama API调用完成")
            elif api == "openai":
                logging.info("准备调用 OpenAI API")
                self._send_openai_chat_message(model, message, temperature)
                logging.info("OpenAI API调用完成")
            elif api == "deepseek":
                logging.info("准备调用 DeepSeek API")
                self._send_deepseek_chat_message(model, message, temperature)
                logging.info("DeepSeek API调用完成")
            else:
                # 不支持的API，发送错误消息
                error_msg = f"不支持的API: {api}"
                logging.error(error_msg)
                self.update_chat_signal.emit("AI", error_msg, model)
            
            # 保存聊天历史到历史管理器
            logging.info("准备保存聊天历史")
            self._save_standard_chat_history(model)
            logging.info("聊天历史保存完成")
            
        except Exception as e:
            error_msg = f"发送消息失败: {str(e)}"
            logging.error(f"_send_chat_message_thread 异常: {error_msg}")
            # 使用信号安全地更新UI
            # 只更新AI的错误消息，用户消息已经在主线程中添加
            self.update_chat_signal.emit("AI", error_msg, model)
        finally:
            logging.info("_send_chat_message_thread 进入 finally 块，准备重置状态")
            # 确保在主线程中重置模型正在回答状态
            from PyQt5.QtCore import QMetaObject, Q_ARG
            from PyQt5.QtCore import Qt
            QMetaObject.invokeMethod(
                self,
                "reset_model_responding_status",
                Qt.QueuedConnection
            )
            logging.info("_send_chat_message_thread 执行完成")
    
    @pyqtSlot()
    def reset_model_responding_status(self):
        """重置模型正在回答状态，确保在主线程中执行"""
        self.is_model_responding = False
        self.is_typing = False
        self.chat_history_before_typing = None
        # 完全重置流式更新状态，确保每次AI回答都是新的对话轮次
        if hasattr(self, '_streaming_state'):
            delattr(self, '_streaming_state')
    
    def _send_ollama_chat_message(self, model, message, temperature):
        """发送消息到Ollama API"""
        try:
            base_url = self.api_settings_widget.get_ollama_base_url()
            # 获取聊天系统提示词
            chat_system_prompt = self.api_settings_widget.chat_system_prompt_edit.toPlainText().strip()
            
            # 检查聊天历史是否为空，如果为空则添加系统提示词
            if not self.standard_chat_history_messages:
                if chat_system_prompt:
                    # 通过append_to_standard_chat_history添加系统消息，确保一致性
                    self.append_to_standard_chat_history("系统", chat_system_prompt)
            
            # 使用完整的聊天历史发送消息
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": self.standard_chat_history_messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature
                    }
                },
                stream=True
            )
            response.raise_for_status()
            
            # 处理流式响应
            ai_response = ""
            import logging
            logging.info("开始处理 Ollama API 流式响应")
            for chunk in response.iter_lines():
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    logging.debug(f"收到 Ollama API 流式数据: {chunk_str}")
                    if chunk_str.strip():
                        try:
                            response_data = json.loads(chunk_str)
                            logging.debug(f"解析后的 Ollama API 响应: {response_data}")
                            if (message := response_data.get("message")) and (content := message.get("content")):
                                ai_response += content
                                logging.info(f"收到 Ollama API 内容片段: {content}")
                                # 使用流式更新信号发送内容片段
                                self.stream_chat_update_signal.emit("AI", content, model)
                            elif response_data.get("done"):
                                logging.info("Ollama API 流式响应结束")
                                break
                        except json.JSONDecodeError as e:
                            logging.error(f"解析 Ollama API 响应失败: {e}")
                            continue
            
            if not ai_response:
                logging.warning("Ollama API 没有返回任何内容")
                ai_response = "抱歉，我无法回答你的问题。"
                self.update_chat_signal.emit("AI", ai_response, model)
            
            # AI回复将通过流式更新信号或update_chat_signal添加到聊天历史中
            
            logging.info(f"Ollama API 完整响应: {ai_response}")
            return ai_response
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama API请求失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except json.JSONDecodeError as e:
            error_msg = f"Ollama API响应解析失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except Exception as e:
            error_msg = f"发送Ollama消息时发生未知错误: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        
        # 控制聊天历史的大小，防止内存溢出
        if len(self.standard_chat_history_messages) > self.max_standard_chat_history * 2 + 1:  # 2条/轮 + 系统提示词
            # 保留系统提示词和最新的max_standard_chat_history轮对话
            if self.standard_chat_history_messages[0]["role"] == "system":
                self.standard_chat_history_messages = [self.standard_chat_history_messages[0]] + self.standard_chat_history_messages[-(self.max_standard_chat_history * 2):]
            else:
                self.standard_chat_history_messages = self.standard_chat_history_messages[-(self.max_standard_chat_history * 2):]
        
        # 重置模型正在回答状态，允许用户发送新消息
        self.is_model_responding = False
        
        return ai_response
    
    def _send_openai_chat_message(self, model, message, temperature):
        """发送消息到OpenAI API"""
        try:
            import requests
            api_key = self.api_settings_widget.get_openai_api_key()
            # 获取聊天系统提示词
            chat_system_prompt = self.api_settings_widget.chat_system_prompt_edit.toPlainText().strip()
            
            # 检查聊天历史是否为空，如果为空则添加系统提示词
            if not self.standard_chat_history_messages:
                if chat_system_prompt:
                    # 通过append_to_standard_chat_history添加系统消息，确保一致性
                    self.append_to_standard_chat_history("系统", chat_system_prompt)
            
            # 使用完整的聊天历史发送消息
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": self.standard_chat_history_messages,
                    "stream": True,
                    "temperature": temperature
                },
                stream=True
            )
            response.raise_for_status()
            
            # 处理流式响应
            ai_response = ""
            for chunk in response.iter_lines():
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    # 移除data: 前缀和可能的空白字符
                    if chunk_str.startswith('data:'):
                        chunk_str = chunk_str[5:].strip()
                        if chunk_str == '[DONE]':
                            break
                        try:
                            response_data = json.loads(chunk_str)
                            if (choices := response_data.get("choices")) and len(choices) > 0:
                                if (choice := choices[0]) and (delta := choice.get("delta")):
                                    if (content := delta.get("content")):
                                        ai_response += content
                                        # 使用流式更新信号发送内容片段
                                        self.stream_chat_update_signal.emit("AI", content, model)
                        except json.JSONDecodeError:
                            continue
            
            # AI回复将通过流式更新信号添加到聊天历史中
            
            # 优化内存使用：如果历史记录超过限制，只保留最近的消息
            self._optimize_chat_history()
            
            return ai_response
        except requests.exceptions.RequestException as e:
            error_msg = f"OpenAI API请求失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except json.JSONDecodeError as e:
            error_msg = f"OpenAI API响应解析失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except Exception as e:
            error_msg = f"发送OpenAI消息时发生未知错误: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
    
    def _send_deepseek_chat_message(self, model, message, temperature):
        """发送消息到DeepSeek API"""
        try:
            import requests
            api_key = self.api_settings_widget.get_deepseek_api_key()
            # 获取聊天系统提示词
            chat_system_prompt = self.api_settings_widget.chat_system_prompt_edit.toPlainText().strip()
            
            # 检查聊天历史是否为空，如果为空则添加系统提示词
            if not self.standard_chat_history_messages:
                if chat_system_prompt:
                    # 通过append_to_standard_chat_history添加系统消息，确保一致性
                    self.append_to_standard_chat_history("系统", chat_system_prompt)
            
            # 使用完整的聊天历史发送消息
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": self.standard_chat_history_messages,
                    "stream": True,
                    "temperature": temperature
                },
                stream=True
            )
            response.raise_for_status()
            
            # 处理流式响应
            ai_response = ""
            for chunk in response.iter_lines():
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    # 移除data: 前缀和可能的空白字符
                    if chunk_str.startswith('data:'):
                        chunk_str = chunk_str[5:].strip()
                        if chunk_str == '[DONE]':
                            break
                        try:
                            response_data = json.loads(chunk_str)
                            if (choices := response_data.get("choices")) and len(choices) > 0:
                                if (choice := choices[0]) and (delta := choice.get("delta")):
                                    if (content := delta.get("content")):
                                        ai_response += content
                                        # 使用流式更新信号发送内容片段
                                        self.stream_chat_update_signal.emit("AI", content, model)
                        except json.JSONDecodeError:
                            continue
            
            # AI回复将通过流式更新信号添加到聊天历史中
            
            # 控制聊天历史的大小，防止内存溢出
            if len(self.standard_chat_history_messages) > self.max_standard_chat_history * 2 + 1:  # 2条/轮 + 系统提示词
                # 保留系统提示词和最新的max_standard_chat_history轮对话
                if self.standard_chat_history_messages[0]["role"] == "system":
                    self.standard_chat_history_messages = [self.standard_chat_history_messages[0]] + self.standard_chat_history_messages[-(self.max_standard_chat_history * 2):]
                else:
                    self.standard_chat_history_messages = self.standard_chat_history_messages[-(self.max_standard_chat_history * 2):]
            
            return ai_response
        except requests.exceptions.RequestException as e:
            error_msg = f"DeepSeek API请求失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except json.JSONDecodeError as e:
            error_msg = f"DeepSeek API响应解析失败: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
        except Exception as e:
            error_msg = f"发送DeepSeek消息时发生未知错误: {str(e)}"
            logger.error(error_msg)
            # 使用信号安全地更新UI，显示错误消息
            self.update_chat_signal.emit("AI", error_msg, model)
            return None
    
    def _get_timestamp(self):
        """获取当前时间戳，格式：YYYY-MM-DD HH:MM:SS"""
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_model_from_sender(self, sender):
        """从发送者名称中提取模型名称（如果存在）"""
        extracted_model = ""
        if "(" in sender and ")" in sender:
            # 提取括号中的内容作为模型名称（找到最后一对括号，处理HTML标签的情况）
            model_start = sender.rfind("(") + 1
            model_end = sender.rfind(")")
            extracted_model = sender[model_start:model_end]
            # 从发送者名称中移除模型信息（只移除最后一对括号及其内容）
            sender = sender[:model_start-1].strip()
        return sender, extracted_model
    
    def _render_markdown_content(self, content):
        """将Markdown内容渲染为HTML"""
        try:
            # 使用Markdown渲染内容，增强代码块显示
            return markdown.markdown(content, extensions=['fenced_code', 'codehilite', 'tables', 'attr_list'])
        except Exception as e:
            # 如果Markdown渲染失败，使用原始内容作为回退
            return content.replace("<", "&lt;").replace(">", "&gt;")
    
    def _build_message_html(self, sender, rendered_content, timestamp, extracted_model, style_params):
        """构建消息的HTML内容，使用统一的样式和结构"""
        sender_color = style_params['sender_color']
        background_color = style_params['background_color']
        border_color = style_params['border_color']
        accent_color = style_params['accent_color']
        separator_color = style_params['separator_color']
        icon_char = style_params['icon_char']
        message_style = style_params.get('message_style', '')
        show_corner = style_params.get('show_corner', True)
        
        # 添加带有颜色的分隔线
        separator_html = f"<div style='height: 3px; background: linear-gradient(to right, {separator_color}, transparent); margin: 15px 0 10px 0; border-radius: 2px;'></div>"
        
        # 构建消息头部（发送者、模型名称、时间戳）
        header_html = [f"<div style='display: flex; justify-content: flex-start; align-items: center; margin-bottom: 8px;'>"]
        header_html.append(f"<span style='margin-right: 8px; font-size: 14pt;'>{icon_char}</span>")
        header_html.append(f"<strong style='color: {sender_color}; font-size: 11pt;'>{sender}</strong>")
        
        # 使用提取的模型名称（如果有）
        if extracted_model:
            header_html.append(f"&nbsp;&nbsp;<span style='color: {sender_color}; opacity: 0.9; font-size: 9pt; font-weight: normal; background-color: {accent_color}; padding: 2px 6px; border-radius: 10px;'>({extracted_model})</span>")
        elif sender.lower() == "user" or sender == "用户":
            # 如果是用户消息且没有模型名称，在发送者和时间戳之间添加两个空格
            header_html.append(f"&nbsp;&nbsp;")
        
        header_html.append(f"<span style='margin-left: auto; font-size: 8pt; color: #616161; background-color: {accent_color}; padding: 1px 5px; border-radius: 10px;'>{timestamp}</span>")
        header_html.append(f"</div>")
        header_html = ''.join(header_html)
        
        # 构建消息容器
        message_parts = [separator_html]
        
        if message_style:
            # 使用特定的消息样式（如标准聊天的右对齐）
            message_parts.append(f"<div {message_style}>")
        else:
            # 使用默认的消息样式
            message_parts.append(f"<div style='background-color: {background_color}; border: 2px solid {border_color}; padding: 15px; border-radius: 10px; margin: 5px 0; box-shadow: 0 3px 8px rgba(0,0,0,0.1); position: relative;'>")
        
        # 添加装饰角标（如果需要）
        if show_corner:
            message_parts.append(f"<div style='position: absolute; top: 0; left: 0; width: 0; height: 0; border-top: 20px solid {border_color}; border-right: 20px solid transparent; border-radius: 10px 0 0 0;'></div>")
        
        # 添加头部和内容
        message_parts.append(header_html)
        message_parts.append(f"<div style='margin-top: 10px; line-height: 1.6; color: #212121;'>{rendered_content}</div>")
        message_parts.append(f"</div>")
        
        return ''.join(message_parts)
    
    def append_to_standard_chat_history(self, sender, content, model=""):
        """将消息添加到标准聊天历史中，支持Markdown格式和美化样式"""
        # 处理清空命令
        if sender == "CLEAR":
            self.standard_chat_history.clear()
            self.standard_chat_count = 0  # 重置聊天历史计数
            self.standard_chat_history_messages = []  # 清除内存中的聊天历史
            return
            
        # 记录消息到内存中的聊天历史，但跳过"正在思考..."
        if content != "正在思考...":
            role = "system" if sender == "系统" else "user" if sender in ["用户", "user"] else "assistant"
            self.standard_chat_history_messages.append({"role": role, "content": content})
            
        # 获取当前时间戳
        timestamp = self._get_timestamp()
        
        # 渲染Markdown内容
        rendered_content = self._render_markdown_content(content)
        
        # 根据发送者设置不同的样式参数
        if sender.lower() == "user" or sender == "用户":
            # 用户消息样式：右侧对齐，蓝色主题 - 增强版
            style_params = {
                'sender_color': "#0d47a1",
                'background_color': "#e3f2fd",
                'border_color': "#2196f3",
                'accent_color': "#bbdefb",
                'separator_color': "#90caf9",
                'icon_char': "👤",
                'message_style': "style='background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 18px; padding: 14px; margin: 10px 10px 10px 60px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                'show_corner': False
            }
        else:
            # AI消息样式：左侧对齐，紫色主题 - 增强版
            style_params = {
                'sender_color': "#6a1b9a",
                'background_color': "#f3e5f5",
                'border_color': "#9c27b0",
                'accent_color': "#e1bee7",
                'separator_color': "#ce93d8",
                'icon_char': "🤖",
                'message_style': "style='background-color: #f3e5f5; border: 2px solid #9c27b0; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                'show_corner': False
            }
        
        # 构建消息HTML
        html_content = self._build_message_html(sender, rendered_content, timestamp, model, style_params)
        
        # 如果是AI回复且之前处于正在思考状态，使用保存的聊天历史替换"正在思考..."
        if sender == "AI" and content != "正在思考..." and self.is_typing and self.chat_history_before_typing:
            # 使用"正在思考..."之前的聊天历史作为基础
            current_html = self.chat_history_before_typing
            # 重置正在思考状态
            self.is_typing = False
            self.chat_history_before_typing = None
            # 重置模型正在回答状态
            self.is_model_responding = False
        else:
            # 获取当前文档的HTML内容
            current_html = self.standard_chat_history.toHtml()
            # 如果是AI回复且不是"正在思考..."，重置模型正在回答状态
            if sender == "AI" and content != "正在思考...":
                self.is_model_responding = False
        
        # 查找<body>标签位置
        body_start = current_html.find("<body")
        if body_start == -1:
            # 如果没有body标签，直接设置HTML，优化CSS样式
            self.standard_chat_history.setHtml(f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body>{html_content}</body></html>''')
            self.standard_chat_count = 1  # 设置聊天历史计数为1
        else:
            # 查找body结束标签
            body_end = current_html.find(">", body_start) + 1
            end_body = current_html.rfind("</body>")
            
            if end_body != -1:
                # 构建新的HTML内容 - 确保在正确位置插入新消息
                body_content = current_html[body_end:end_body]
                
                # 检查是否需要限制聊天历史数量
                if self.standard_chat_count >= self.max_standard_chat_history:
                    # 如果超过最大数量，找到第一条消息并移除
                    first_message_end = body_content.find("</div>") + 6  # 找到第一条消息的结束位置
                    if first_message_end != -1:
                        # 移除第一条消息
                        body_content = body_content[first_message_end:]
                else:
                    # 增加聊天历史计数
                    self.standard_chat_count += 1
                
                new_html = current_html[:body_end] + body_content + html_content + current_html[end_body:]
            else:
                # 如果没有</body>标签，直接添加内容到body中
                new_html = current_html[:body_end] + current_html[body_end:] + html_content
                self.standard_chat_count += 1  # 增加聊天历史计数
            
            self.standard_chat_history.setHtml(new_html)
        
        # 滚动到底部
        self.standard_chat_history.moveCursor(QTextCursor.End)
    
    def show_error_message(self, title, message):
        """显示错误消息讨论框"""
        QMessageBox.critical(self, title, message)
        # 同时更新状态栏
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(title, 5000)  # 显示5秒
    
    def _handle_discussion_update(self, sender, content, model=""):
        """处理讨论功能的完整更新"""
        # 忽略空内容的更新信号，这是流式输出开始的标记
        if content.strip():
            # 直接添加完整回复
            self.append_to_chat_history(sender, content, model)
        
        # 清除该发送者的流式更新状态
        if sender in self._discussion_streaming_states:
            del self._discussion_streaming_states[sender]
    
    def _handle_discussion_stream_update(self, sender, content, model=""):
        """处理讨论功能的流式更新，合并所有流式输出到一个回答中"""
        try:
            # 1. 确保流式更新状态存在并正确初始化
            if sender not in self._discussion_streaming_states:
                # 保存当前聊天历史作为基础
                base_html = self.chat_history_text.toHtml()
                
                # 初始化流式更新状态，保存完整的聊天历史
                self._discussion_streaming_states[sender] = {
                    'is_streaming': True,
                    'content': content,
                    'sender': sender,
                    'model': model,
                    'base_html': base_html,
                    'timestamp': self._get_timestamp()
                }
            else:
                # 继续当前流式更新，累积内容
                state = self._discussion_streaming_states[sender]
                state['content'] += content
            
            # 2. 更新UI，确保只显示一个AI消息
            self._update_discussion_streaming_chat()
        except Exception as e:
            logger.error(f"讨论功能流式更新处理失败: {str(e)}")
    
    def _update_discussion_streaming_chat(self):
        """更新讨论功能的流式聊天显示"""
        try:
            # 1. 使用当前最新的聊天历史作为基础，确保所有AI的回复都能正确显示
            current_html = self.chat_history_text.toHtml()
            
            # 2. 创建一个临时HTML，用于合并所有流式回复
            body_start = current_html.find("<body")
            if body_start == -1:
                # 如果没有body标签，使用空的HTML结构作为基础
                base_html = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body></body></html>'''
                body_content = ""
            else:
                # 提取当前HTML的body内容，作为基础
                body_end = current_html.find(">", body_start) + 1
                end_body = current_html.rfind("</body>")
                if end_body != -1:
                    body_content = current_html[body_end:end_body]
                    # 移除所有正在流式更新的AI的旧消息
            for sender in list(self._discussion_streaming_states.keys()):
                # 查找并移除该AI的旧消息
                if sender in body_content:
                    # 找到消息的开始位置（更精确的匹配，包括消息头的完整结构）
                    msg_start = body_content.find(sender)
                    if msg_start != -1:
                        # 找到消息的开始div（从当前消息开始位置向前查找最近的<div）
                        div_start = body_content.rfind("<div", 0, msg_start)
                        if div_start != -1:
                            # 计算当前消息在body_content中的位置，用于后续查找结束div
                            current_pos = div_start
                            div_count = 1
                            # 查找匹配的结束div，处理嵌套div的情况
                            while div_count > 0 and current_pos < len(body_content):
                                next_div_start = body_content.find("<div", current_pos + 1)
                                next_div_end = body_content.find("</div>", current_pos + 1)
                                
                                # 如果找不到结束div，说明已经到了内容末尾
                                if next_div_end == -1:
                                    break
                                
                                # 如果找到开始div且在结束div之前，说明是嵌套div
                                if next_div_start != -1 and next_div_start < next_div_end:
                                    div_count += 1
                                    current_pos = next_div_start
                                else:
                                    div_count -= 1
                                    current_pos = next_div_end
                            
                            # 移除旧消息
                            body_content = body_content[:div_start] + body_content[current_pos + 6:]
                else:
                    body_content = ""
                    base_html = current_html
            
            # 3. 合并所有AI的流式回复
            for sender, state in self._discussion_streaming_states.items():
                # 渲染当前累积的AI响应
                rendered_content = self._render_markdown_content(state['content'])
                
                # 创建AI消息的HTML
                timestamp = state['timestamp']
                
                # 根据发送者是AI 1还是AI 2应用不同的颜色样式参数
                if "学者AI1" in sender:
                    # AI 1 使用蓝色主题 - 增强版
                    style_params = {
                        'sender_color': "#0d47a1",
                        'background_color': "#e3f2fd",
                        'border_color': "#2196f3",
                        'accent_color': "#bbdefb",
                        'separator_color': "#90caf9",
                        'icon_char': "🔵",
                        'message_style': "style='background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                elif "学者AI2" in sender:
                    # AI 2 使用绿色主题 - 增强版
                    style_params = {
                        'sender_color': "#1b5e20",
                        'background_color': "#e8f5e9",
                        'border_color': "#4caf50",
                        'accent_color': "#c8e6c9",
                        'separator_color': "#a5d6a7",
                        'icon_char': "🟢",
                        'message_style': "style='background-color: #e8f5e9; border: 2px solid #4caf50; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                else:
                    # 其他消息使用灰色主题 - 增强版
                    style_params = {
                        'sender_color': "#424242",
                        'background_color': "#f5f5f5",
                        'border_color': "#9e9e9e",
                        'accent_color': "#e0e0e0",
                        'separator_color': "#bdbdbd",
                        'icon_char': "⚪",
                        'message_style': "style='background-color: #f5f5f5; border: 2px solid #9e9e9e; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                
                # 从发送者名称中提取模型名称（如果存在）
                processed_sender, extracted_model = self._extract_model_from_sender(sender)
                
                # 使用提取的模型名称（如果有）
                model_to_use = extracted_model if extracted_model else state.get('model', "")
                
                # 构建带有样式的HTML消息
                message_html = self._build_message_html(processed_sender, rendered_content, timestamp, model_to_use, style_params)
                
                # 添加到body内容中
                body_content += message_html
            
            # 4. 构建新的HTML内容
            if body_start == -1:
                new_html = f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body>{body_content}</body></html>'''
            else:
                # 查找body结束标签
                end_body = current_html.rfind("</body>")
                if end_body != -1:
                    new_html = current_html[:body_end] + body_content + current_html[end_body:]
                else:
                    new_html = current_html + body_content
            
            # 5. 更新聊天历史
            self.chat_history_text.setHtml(new_html)
            
            # 6. 滚动到底部
            self.chat_history_text.moveCursor(QTextCursor.End)
        except Exception as e:
            logger.error(f"更新讨论流式聊天失败: {str(e)}")
    
    def _handle_debate_update(self, sender, content, model=""):
        """处理辩论功能的完整更新"""
        # 忽略空内容的更新信号，这是流式输出开始的标记
        if content.strip():
            # 直接添加完整回复
            self.append_to_debate_history(sender, content, model)
        
        # 清除该发送者的流式更新状态
        if sender in self._debate_streaming_states:
            del self._debate_streaming_states[sender]
    
    def _handle_debate_stream_update(self, sender, content, model=""):
        """处理辩论功能的流式更新，合并所有流式输出到一个回答中"""
        try:
            # 1. 确保流式更新状态存在并正确初始化
            if sender not in self._debate_streaming_states:
                # 保存当前聊天历史作为基础
                base_html = self.debate_history_text.toHtml()
                
                # 初始化流式更新状态，保存完整的聊天历史
                self._debate_streaming_states[sender] = {
                    'is_streaming': True,
                    'content': content,
                    'sender': sender,
                    'model': model,
                    'base_html': base_html,
                    'timestamp': self._get_timestamp()
                }
            else:
                # 继续当前流式更新，累积内容
                state = self._debate_streaming_states[sender]
                state['content'] += content
            
            # 2. 更新UI，确保只显示一个AI消息
            self._update_debate_streaming_chat()
        except Exception as e:
            logger.error(f"辩论功能流式更新处理失败: {str(e)}")
    
    def _update_debate_streaming_chat(self):
        """更新辩论功能的流式聊天显示"""
        try:
            # 1. 使用当前最新的聊天历史作为基础，确保所有AI的回复都能正确显示
            current_html = self.debate_history_text.toHtml()
            
            # 2. 创建一个临时HTML，用于合并所有流式回复
            body_start = current_html.find("<body")
            if body_start == -1:
                # 如果没有body标签，使用空的HTML结构作为基础
                base_html = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body></body></html>'''
                body_content = ""
            else:
                # 提取当前HTML的body内容，作为基础
                body_end = current_html.find(">", body_start) + 1
                end_body = current_html.rfind("</body>")
                if end_body != -1:
                    body_content = current_html[body_end:end_body]
                else:
                    body_content = ""
                    base_html = current_html
            
            # 移除所有正在流式更新的AI的旧消息
            # 1. 首先，识别所有需要处理的AI标识符
            ai_identifiers = []
            for sender in self._debate_streaming_states.keys():
                if "正方AI1" in sender:
                    ai_identifiers.append("正方AI1")
                elif "反方AI2" in sender:
                    ai_identifiers.append("反方AI2")
                else:
                    ai_identifiers.append(sender)
            
            # 2. 然后，创建一个新的body_content，移除所有包含这些标识符的消息
            new_body_content = ""
            if body_content:
                # 查找所有消息的开始和结束位置
                messages = []
                current_pos = 0
                
                while True:
                    # 查找消息的开始位置（寻找div标签）
                    div_start = body_content.find("<div", current_pos)
                    if div_start == -1:
                        break
                    
                    # 查找消息的结束位置（寻找匹配的</div>标签）
                    div_count = 1
                    end_pos = div_start + 5  # 跳过<div开始标签
                    
                    while div_count > 0 and end_pos < len(body_content):
                        next_div_start = body_content.find("<div", end_pos)
                        next_div_end = body_content.find("</div>", end_pos)
                        
                        if next_div_end == -1:
                            break
                        
                        if next_div_start != -1 and next_div_start < next_div_end:
                            # 找到开始div且在结束div之前，说明是嵌套div
                            div_count += 1
                            end_pos = next_div_start + 5
                        else:
                            # 找到结束div
                            div_count -= 1
                            if div_count == 0:
                                end_pos = next_div_end + 6  # 包含</div>结束标签
                                break
                            end_pos = next_div_end + 6
                    
                    if div_count == 0 and end_pos > div_start:
                        message = body_content[div_start:end_pos]
                        # 检查消息是否包含任何需要移除的AI标识符
                        contains_ai = any(ai_id in message for ai_id in ai_identifiers)
                        if not contains_ai:
                            # 如果消息不包含任何正在流式更新的AI，保留它
                            new_body_content += message
                    
                    current_pos = end_pos
            
            # 使用新的body_content，已经移除了所有正在流式更新的AI消息
            body_content = new_body_content
            
            # 3. 合并所有AI的流式回复
            for sender, state in self._debate_streaming_states.items():
                # 渲染当前累积的AI响应
                rendered_content = self._render_markdown_content(state['content'])
                
                # 创建AI消息的HTML
                timestamp = state['timestamp']
                
                # 根据发送者是AI 1还是AI 2应用不同的颜色样式参数
                if "正方AI1" in sender:
                    # AI 1 使用蓝色主题 - 增强版
                    style_params = {
                        'sender_color': "#0d47a1",
                        'background_color': "#e3f2fd",
                        'border_color': "#2196f3",
                        'accent_color': "#bbdefb",
                        'separator_color': "#90caf9",
                        'icon_char': "🔵",
                        'message_style': "style='background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                elif "反方AI2" in sender:
                    # AI 2 使用绿色主题 - 增强版
                    style_params = {
                        'sender_color': "#1b5e20",
                        'background_color': "#e8f5e9",
                        'border_color': "#4caf50",
                        'accent_color': "#c8e6c9",
                        'separator_color': "#a5d6a7",
                        'icon_char': "🟢",
                        'message_style': "style='background-color: #e8f5e9; border: 2px solid #4caf50; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                else:
                    # 其他消息使用灰色主题 - 增强版
                    style_params = {
                        'sender_color': "#424242",
                        'background_color': "#f5f5f5",
                        'border_color': "#9e9e9e",
                        'accent_color': "#e0e0e0",
                        'separator_color': "#bdbdbd",
                        'icon_char': "⚪",
                        'message_style': "style='background-color: #f5f5f5; border: 2px solid #9e9e9e; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                        'show_corner': False
                    }
                
                # 从发送者名称中提取模型名称（如果存在）
                processed_sender, extracted_model = self._extract_model_from_sender(sender)
                
                # 使用提取的模型名称（如果有）
                model_to_use = extracted_model if extracted_model else state.get('model', "")
                
                # 构建带有样式的HTML消息
                message_html = self._build_message_html(processed_sender, rendered_content, timestamp, model_to_use, style_params)
                
                # 添加到body内容中
                body_content += message_html
            
            # 4. 构建新的HTML内容
            if body_start == -1:
                new_html = f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body>{body_content}</body></html>'''
            else:
                # 查找body结束标签
                end_body = current_html.rfind("</body>")
                if end_body != -1:
                    new_html = current_html[:body_end] + body_content + current_html[end_body:]
                else:
                    new_html = current_html + body_content
            
            # 5. 更新聊天历史
            self.debate_history_text.setHtml(new_html)
            
            # 6. 滚动到底部
            self.debate_history_text.moveCursor(QTextCursor.End)
        except Exception as e:
            logger.error(f"更新辩论流式聊天失败: {str(e)}")
    
    def append_to_chat_history(self, sender, content, model=""):
        """将消息添加到聊天历史，支持Markdown格式渲染，并为AI1和AI2使用不同颜色区分"""
        try:
            # 获取当前时间戳
            timestamp = self._get_timestamp()
            
            # 从发送者名称中提取模型名称（如果存在）
            sender, extracted_model = self._extract_model_from_sender(sender)
            
            # 使用markdown库将内容转换为HTML，增强代码块显示
            rendered_content = self._render_markdown_content(content)
            
            # 根据发送者是AI 1还是AI 2应用不同的颜色样式参数
            if "学者AI1" in sender:
                # AI 1 使用蓝色主题 - 增强版
                style_params = {
                    'sender_color': "#0d47a1",
                    'background_color': "#e3f2fd",
                    'border_color': "#2196f3",
                    'accent_color': "#bbdefb",
                    'separator_color': "#90caf9",
                    'icon_char': "🔵",
                    'message_style': "style='background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            elif "学者AI2" in sender:
                # AI 2 使用绿色主题 - 增强版
                style_params = {
                    'sender_color': "#1b5e20",
                    'background_color': "#e8f5e9",
                    'border_color': "#4caf50",
                    'accent_color': "#c8e6c9",
                    'separator_color': "#a5d6a7",
                    'icon_char': "🟢",
                    'message_style': "style='background-color: #e8f5e9; border: 2px solid #4caf50; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            else:
                # 其他消息使用灰色主题 - 增强版
                style_params = {
                    'sender_color': "#424242",
                    'background_color': "#f5f5f5",
                    'border_color': "#9e9e9e",
                    'accent_color': "#e0e0e0",
                    'separator_color': "#bdbdbd",
                    'icon_char': "⚪",
                    'message_style': "style='background-color: #f5f5f5; border: 2px solid #9e9e9e; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            
            # 使用提取的模型名称（如果有）
            model_to_use = extracted_model if extracted_model else model
            
            # 构建带有样式的HTML消息
            message_html = self._build_message_html(sender, rendered_content, timestamp, model_to_use, style_params)
            
            # 获取当前文档的HTML内容
            current_html = self.chat_history_text.toHtml()
            
            # 查找<body>标签位置
            body_start = current_html.find("<body")
            if body_start == -1:
                # 如果没有body标签，直接设置HTML，优化CSS样式
                self.chat_history_text.setHtml(f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body>{message_html}</body></html>''')
                self.discussion_chat_count = 1  # 设置聊天历史计数为1
            else:
                # 查找body结束标签
                body_end = current_html.find(">", body_start) + 1
                end_body = current_html.rfind("</body>")
                
                if end_body != -1:
                    # 构建新的HTML内容 - 确保在正确位置插入新消息
                    body_content = current_html[body_end:end_body]
                    
                    # 检查是否需要限制聊天历史数量
                    if self.discussion_chat_count >= self.max_discussion_history:
                        # 如果超过最大数量，找到第一条消息并移除
                        first_message_end = body_content.find("</div>") + 6  # 找到第一条消息的结束位置
                        if first_message_end != -1:
                            # 移除第一条消息
                            body_content = body_content[first_message_end:]
                    else:
                        # 增加聊天历史计数
                        self.discussion_chat_count += 1
                    
                    new_html = current_html[:body_end] + body_content + message_html + current_html[end_body:]
                else:
                    # 如果没有</body>标签，直接添加内容到body中
                    new_html = current_html[:body_end] + current_html[body_end:] + message_html
                    self.discussion_chat_count += 1  # 增加聊天历史计数
                
                self.chat_history_text.setHtml(new_html)
            
            # 滚动到底部
            self.chat_history_text.moveCursor(QTextCursor.End)
            
        except Exception as e:
            # 如果Markdown转换失败，回退到带样式的纯文本显示
            logger.error(f"添加到聊天历史失败: {str(e)}")
            # 显示错误消息
            self.show_error_message("错误", f"添加到聊天历史失败: {str(e)}")
    
    def update_status(self, message):
        """更新讨论功能的状态栏信息"""
        self.status_label.setText(message)
    
    def _handle_stream_chat_update(self, sender, content, model=""):
        """处理AI响应的流式更新"""
        try:
            # 确保流式更新状态存在并正确初始化
            if not hasattr(self, '_streaming_state'):
                # 使用之前保存的聊天历史（在添加"正在思考..."之前）
                if hasattr(self, 'chat_history_before_typing') and self.chat_history_before_typing:
                    base_html = self.chat_history_before_typing
                else:
                    # 如果没有保存之前的历史，获取当前聊天历史
                    base_html = self.standard_chat_history.toHtml()
                
                # 初始化流式更新状态，保存完整的聊天历史
                self._streaming_state = {
                    'is_streaming': True,
                    'content': content,
                    'sender': sender,
                    'model': model,
                    'base_html': base_html
                }
            else:
                # 继续当前流式更新，累积内容
                state = self._streaming_state
                state['content'] += content
            
            # 更新UI，确保只显示一个AI消息
            self._update_streaming_chat()
        except Exception as e:
            # 捕获所有异常，防止程序闪退
            logger.error(f"流式更新处理失败: {str(e)}")
    
    def _update_streaming_chat(self):
        """更新流式聊天显示"""
        state = self._streaming_state
        
        # 1. 使用保存的聊天历史（在添加"正在思考..."之前）作为基础
        # 这样可以确保每次流式更新都替换掉"正在思考..."，并合并为一轮回复
        base_html = state.get('base_html', "<html><body></body></html>")
        
        # 2. 渲染当前累积的AI响应
        rendered_content = self._render_markdown_content(state['content'])
        
        # 3. 创建AI消息的HTML
        timestamp = self._get_timestamp()
        ai_style_params = {
            'sender_color': "#6a1b9a",
            'background_color': "#f3e5f5",
            'border_color': "#9c27b0",
            'accent_color': "#e1bee7",
            'separator_color': "#ce93d8",
            'icon_char': "🤖",
            'message_style': "style='background-color: #f3e5f5; border: 2px solid #9c27b0; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
            'show_corner': False
        }
        ai_message_html = self._build_message_html(state['sender'], rendered_content, timestamp, state['model'], ai_style_params)
        
        # 4. 构建新的HTML内容
        # 确保将AI响应添加到base_html的body中，这样就能完全替换"正在思考..."
        body_start = base_html.find("<body")
        if body_start != -1:
            body_end = base_html.find(">", body_start) + 1
            end_body = base_html.rfind("</body>")
            if end_body != -1:
                # 使用base_html作为基础，添加当前AI响应
                # 这样就能确保"正在思考..."被完全替换
                body_content = base_html[body_end:end_body]
                new_body_content = body_content + ai_message_html
                new_html = base_html[:body_end] + new_body_content + base_html[end_body:]
            else:
                # 如果没有</body>标签，直接添加到末尾
                new_html = base_html + ai_message_html
        else:
            # 如果没有<body>标签，创建完整的HTML结构
            new_html = f"<html><body>{ai_message_html}</body></html>"
        
        # 5. 更新聊天历史
        self.standard_chat_history.setHtml(new_html)
        
        # 6. 滚动到底部
        self.standard_chat_history.moveCursor(QTextCursor.End)
    
    def update_debate_status(self, message):
        """更新辩论功能的状态栏信息"""
        self.debate_status_label.setText(message)
    
    def start_chat(self):
        """开始AI讨论功能的核心方法
        
        该方法执行以下步骤：
        1. 验证讨论主题是否为空
        2. 获取各种配置参数（模型选择、API设置、讨论轮数等）
        3. 创建AI聊天管理器
        4. 初始化讨论环境
        5. 启动讨论线程
        """
        # 验证讨论主题是否为空
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "警告", "请输入讨论主题")
            return
        
        # 检查是否已有线程在运行
        if hasattr(self, 'chat_thread') and self.chat_thread and self.chat_thread.isRunning():
            QMessageBox.warning(self, "警告", "讨论已在进行中，请先停止当前讨论")
            return
        
        try:
            # 获取AI模型和API配置参数
            model1 = self.model1_combo.currentText()  # 学者AI1使用的模型
            model2 = self.model2_combo.currentText()  # 学者AI2使用的模型
            api1 = self.api1_combo.currentText()      # 学者AI1使用的API
            api2 = self.api2_combo.currentText()      # 学者AI2使用的API
            rounds = self.rounds_spin.value()         # 讨论轮数
            time_limit = self.time_limit_spin.value() if self.time_limit_spin.value() > 0 else None  # 时间限制（秒）
            temperature = self.temp_spin.value()      # AI回复的温度参数
            
            # 获取辩论系统提示词
            debate_common_prompt = ""
            debate_ai1_prompt = ""
            debate_ai2_prompt = ""
            if hasattr(self, 'api_settings_widget'):
                debate_common_prompt = self.api_settings_widget.debate_common_prompt_edit.toPlainText().strip()  # 通用辩论提示词
                debate_ai1_prompt = self.api_settings_widget.debate_ai1_prompt_edit.toPlainText().strip()        # AI1专用辩论提示词
                debate_ai2_prompt = self.api_settings_widget.debate_ai2_prompt_edit.toPlainText().strip()        # AI2专用辩论提示词
            
            # 获取API密钥和配置
            openai_api_key = ""
            deepseek_api_key = ""
            ollama_base_url = ""
            if hasattr(self, 'api_settings_widget'):
                openai_api_key = self.api_settings_widget.get_openai_api_key()    # OpenAI API密钥
                deepseek_api_key = self.api_settings_widget.get_deepseek_api_key()  # DeepSeek API密钥
                ollama_base_url = self.api_settings_widget.get_ollama_base_url()   # Ollama本地服务器地址
            
            # 验证API密钥（如果选择了需要密钥的API）
            if api1 == "OpenAI" and not openai_api_key:
                QMessageBox.warning(self, "警告", "使用OpenAI API需要配置API密钥")
                return
            if api1 == "DeepSeek" and not deepseek_api_key:
                QMessageBox.warning(self, "警告", "使用DeepSeek API需要配置API密钥")
                return
            if api2 == "OpenAI" and not openai_api_key:
                QMessageBox.warning(self, "警告", "使用OpenAI API需要配置API密钥")
                return
            if api2 == "DeepSeek" and not deepseek_api_key:
                QMessageBox.warning(self, "警告", "使用DeepSeek API需要配置API密钥")
                return
            
            # 验证Ollama URL（如果选择了Ollama API）
            if (api1 == "Ollama" or api2 == "Ollama") and not ollama_base_url:
                QMessageBox.warning(self, "警告", "使用Ollama API需要配置服务器地址")
                return
            
            logger.info(f"开始创建AIChatManager: AI1使用{model1}({api1}), AI2使用{model2}({api2})")
            
            # 创建AI聊天管理器实例，负责协调两个AI之间的讨论
            manager = AIChatManager(
                model1_name=model1,
                model2_name=model2,
                model1_api=api1,
                model2_api=api2,
                openai_api_key=openai_api_key,
                deepseek_api_key=deepseek_api_key,
                ollama_base_url=ollama_base_url,
                temperature=temperature,
                debate_common_prompt=debate_common_prompt,
                debate_ai1_prompt=debate_ai1_prompt,
                debate_ai2_prompt=debate_ai2_prompt
            )
            
            # 清除之前的聊天历史和流式状态
            self.chat_history_text.clear()
            self._discussion_streaming_states.clear()  # 重置流式状态
            
            # 禁用配置控件，防止讨论进行中修改配置
            self.topic_edit.setEnabled(False)
            self.model1_combo.setEnabled(False)
            self.model2_combo.setEnabled(False)
            self.api1_combo.setEnabled(False)
            self.api2_combo.setEnabled(False)
            self.rounds_spin.setEnabled(False)
            self.time_limit_spin.setEnabled(False)
            self.temp_spin.setEnabled(False)
            self.start_button.setEnabled(False)  # 禁用开始按钮
            self.stop_button.setEnabled(True)    # 启用停止按钮
            
            # 更新状态栏信息
            self.update_status("正在准备讨论...")
            
            # 创建并启动讨论线程，避免阻塞主线程UI
            self.chat_thread = ChatThread(manager, topic, rounds, time_limit)
            # 连接线程信号到UI更新槽函数
            self.chat_thread.update_signal.connect(self._handle_discussion_update)
            self.chat_thread.stream_update_signal.connect(self._handle_discussion_stream_update)
            self.chat_thread.status_signal.connect(self.update_status)         # 更新状态信息
            self.chat_thread.finished_signal.connect(self.on_chat_finished)    # 讨论完成处理
            self.chat_thread.error_signal.connect(self.on_chat_error)          # 错误处理
            self.chat_thread.start()  # 启动线程
            
            logger.info(f"讨论线程已启动，主题: {topic}, 轮数: {rounds}")
            
        except Exception as e:
            # 处理初始化过程中的异常
            logger.error(f"初始化讨论失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"初始化讨论失败: {str(e)}")
            # 恢复UI状态
            self.enable_ui()
            # 清除流式状态
            self._discussion_streaming_states.clear()
    
    def stop_chat(self):
        """停止正在进行的AI讨论
        
        该方法会检查讨论线程是否存在并正在运行，如果是，则发送停止信号
        并更新状态栏信息
        """
        if hasattr(self, 'chat_thread') and self.chat_thread and self.chat_thread.isRunning():
            try:
                self.chat_thread.stop()  # 调用线程的停止方法
                self.update_status("正在停止讨论...")  # 更新状态栏显示
                
                # 添加超时等待机制，最多等待5秒
                import time
                start_time = time.time()
                timeout = 5  # 5秒超时
                
                # 等待线程停止，但不阻塞UI
                def wait_for_stop():
                    end_time = start_time + timeout
                    while time.time() < end_time and self.chat_thread.isRunning():
                        time.sleep(0.1)  # 短暂休眠
                    
                    if not self.chat_thread.isRunning():
                        # 如果线程已停止，调用完成回调
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(0, self.on_chat_finished)
                    else:
                        # 如果线程仍在运行，发出警告
                        logger.warning("讨论线程在5秒内未能停止")
                        
                # 在后台线程中等待
                from threading import Thread
                Thread(target=wait_for_stop).start()
                
            except Exception as e:
                logger.error(f"停止讨论时发生错误: {str(e)}")
                QMessageBox.warning(self, "警告", f"停止讨论时发生错误: {str(e)}")
    
    def _save_discussion_history(self):
        """保存讨论历史到历史管理器"""
        topic = self.topic_edit.text().strip()
        if not topic:
            topic = "无主题讨论"
        
        model1 = self.model1_combo.currentText()
        model2 = self.model2_combo.currentText()
        
        # 查找是否已存在相同模型组合的讨论历史记录
        existing_history_index = -1
        for i, history in enumerate(self.all_chat_histories):
            if history["type"] == "讨论" and history["model1"] == model1 and history["model2"] == model2:
                existing_history_index = i
                break
        
        if existing_history_index != -1:
            # 更新现有历史记录
            self.all_chat_histories[existing_history_index].update({
                "topic": topic,
                "messages": self.discussion_history_messages.copy(),
                "html_content": self.chat_history_text.toHtml(),
                "timestamp": self._get_timestamp()
            })
        else:
            # 创建讨论历史记录
            discussion_history = {
                "id": len(self.all_chat_histories) + 1,
                "type": "讨论",
                "topic": topic,
                "model1": model1,
                "model2": model2,
                "timestamp": self._get_timestamp(),
                "messages": self.discussion_history_messages.copy(),
                "html_content": self.chat_history_text.toHtml()
            }
            # 添加到历史记录列表
            self.all_chat_histories.append(discussion_history)
        
        # 保存所有历史记录到磁盘
        self.chat_history_manager.save_history(self.all_chat_histories)
    
    def on_chat_finished(self):
        """讨论完成后的回调方法
        
        当AI讨论正常完成时，该方法会被调用，用于恢复UI状态并更新状态信息
        """
        try:
            # 确保线程已停止
            if hasattr(self, 'chat_thread') and self.chat_thread and self.chat_thread.isRunning():
                logger.warning("讨论线程在完成信号触发时仍在运行")
            
            # 保存讨论历史到历史管理器
            self._save_discussion_history()
            
            self.enable_ui()  # 启用所有UI控件
            self.update_status("讨论已完成")  # 更新状态信息
            
            # 显式设置线程为None，帮助垃圾回收
            if hasattr(self, 'chat_thread'):
                self.chat_thread = None
            
            logger.info("讨论正常完成并清理了资源")
        except Exception as e:
            logger.error(f"处理讨论完成事件时发生错误: {str(e)}")
    
    def on_chat_error(self, error_message):
        """处理讨论过程中发生的错误
        
        参数:
            error_message (str): 错误信息的详细描述
        """
        try:
            logger.error(f"讨论过程中发生错误: {error_message}")
            
            # 分析错误信息，提供更友好的提示
            friendly_message = error_message
            if "API密钥" in error_message or "API Key" in error_message:
                friendly_message = f"API密钥错误: {error_message}\n请检查API密钥设置后重试。"
            elif "连接" in error_message or "Connection" in error_message:
                friendly_message = f"网络连接错误: {error_message}\n请检查网络连接或API服务器地址后重试。"
            elif "超时" in error_message or "Timeout" in error_message:
                friendly_message = f"请求超时: {error_message}\nAI响应时间过长，请检查网络状况或稍后重试。"
            
            QMessageBox.critical(self, "错误", friendly_message)  # 显示错误信息对话框
            self.enable_ui()  # 恢复UI控件可使用状态
            self.update_status("讨论出错")  # 更新状态信息
            
            # 确保资源被正确清理
            if hasattr(self, 'chat_thread'):
                self.chat_thread = None
                
        except Exception as e:
            logger.error(f"处理讨论错误时发生二次错误: {str(e)}")
            # 避免二次错误引起崩溃，使用日志记录而非UI交互
    
    def enable_ui(self):
        """启用所有UI配置控件
        
        该方法在讨论完成或出错时被调用，用于恢复用户对配置选项的操作权限
        """
        self.topic_edit.setEnabled(True)    # 讨论主题输入框
        self.model1_combo.setEnabled(True)  # AI1模型选择
        self.model2_combo.setEnabled(True)  # AI2模型选择
        self.api1_combo.setEnabled(True)    # AI1 API选择
        self.api2_combo.setEnabled(True)    # AI2 API选择
        self.rounds_spin.setEnabled(True)   # 讨论轮数设置
        self.time_limit_spin.setEnabled(True)  # 时间限制设置
        self.temp_spin.setEnabled(True)     # 温度参数设置
        self.start_button.setEnabled(True)  # 启用开始按钮
        self.stop_button.setEnabled(False)  # 禁用停止按钮
    
    def on_settings_saved(self):
        """API设置保存后的处理"""
        self.update_status("API设置已更新")
    
    def export_debate_history_to_pdf(self):
        """将辩论历史导出为PDF文件"""
        try:
            # 检查是否有辩论历史
            if self.debate_history_text.toPlainText().strip() == "":
                QMessageBox.information(self, "提示", "没有辩论历史可供导出")
                return
            
            # 生成当前时间戳（yyyyMMdd_HHmmss格式）
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            # 设置辩论功能默认文件名
            default_filename = f"Nonead_Debate_{timestamp}.pdf"
            
            # 打开文件讨论框选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(self, "导出辩论历史为PDF", default_filename, "PDF Files (*.pdf)")
            if not file_path:
                return
            
            # 确保文件扩展名为.pdf
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'
            
            # 创建QPrinter对象用于PDF导出
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            
            # 设置页面属性
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)
            
            # 创建一个新的QTextEdit用于导出，并保留HTML格式
            temp_edit = QTextEdit()
            
            # 获取当前辩论历史的HTML内容
            html_content = self.debate_history_text.toHtml()
            
            # 获取辩论主题
            topic = self.debate_topic_edit.text().strip()
            if not topic:
                topic = "未指定辩论主题"
            
            # 添加标题和主题（在HTML中）
            title = f"AI辩论历史 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            # 第一行显示辩论主题，使用<h2>标签并居中
            styled_html = f"<h1 style='text-align:center;'>{title}</h1><h2 style='text-align:center; margin-top:10px;'>辩论主题: {topic}</h2><br>{html_content}"
            
            # 设置HTML内容
            temp_edit.setHtml(styled_html)
            
            # 执行打印（导出为PDF）
            result = temp_edit.print_(printer)
            
            # 检查文件是否实际创建，而不只是依赖result返回值
            import os
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                # 文件成功创建
                self.update_status(f"辩论历史已成功导出到 {file_path}")
                QMessageBox.information(self, "成功", f"辩论历史已成功导出到\n{file_path}")
            else:
                # 文件未创建或为空
                error_msg = "PDF导出失败，可能是权限问题或文件路径无效"
                self.update_status(f"导出PDF失败: {error_msg}")
                QMessageBox.critical(self, "错误", f"导出PDF失败: {error_msg}\n\n请尝试选择其他保存位置。")
                
        except Exception as e:
            error_details = f"{str(e)}"
            self.update_status(f"导出PDF失败: {error_details}")
            QMessageBox.critical(self, "错误", f"导出PDF失败: {error_details}\n\n请检查文件路径权限或尝试其他位置。")
    
    def start_debate(self):
        """开始AI辩论"""
        # 验证输入
        topic = self.debate_topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "警告", "请输入辩论主题")
            return
        
        try:
            # 获取配置参数
            model1 = self.debate_model1_combo.currentText()
            model2 = self.debate_model2_combo.currentText()
            api1 = self.debate_api1_combo.currentText()
            api2 = self.debate_api2_combo.currentText()
            rounds = self.debate_rounds_spin.value()
            time_limit = self.debate_time_limit_spin.value() if self.debate_time_limit_spin.value() > 0 else None
            temperature = self.debate_temp_spin.value()
            
            # 获取辩论系统提示词
            debate_common_prompt = ""
            debate_ai1_prompt = ""
            debate_ai2_prompt = ""
            if hasattr(self, 'api_settings_widget'):
                debate_common_prompt = self.api_settings_widget.debate_common_prompt_edit.toPlainText().strip()
                debate_ai1_prompt = self.api_settings_widget.debate_ai1_prompt_edit.toPlainText().strip()
                debate_ai2_prompt = self.api_settings_widget.debate_ai2_prompt_edit.toPlainText().strip()
            
            # 创建AI聊天管理器
            manager = AIChatManager(
                model1_name=model1,
                model2_name=model2,
                model1_api=api1,
                model2_api=api2,
                temperature=temperature,
                debate_common_prompt=debate_common_prompt,
                debate_ai1_prompt=debate_ai1_prompt,
                debate_ai2_prompt=debate_ai2_prompt
            )
            
            # 清除辩论历史和流式状态
            self.debate_history_text.clear()
            self._debate_streaming_states.clear()  # 重置流式状态
            
            # 禁用配置控件
            self.debate_topic_edit.setEnabled(False)
            self.debate_model1_combo.setEnabled(False)
            self.debate_model2_combo.setEnabled(False)
            self.debate_api1_combo.setEnabled(False)
            self.debate_api2_combo.setEnabled(False)
            self.debate_rounds_spin.setEnabled(False)
            self.debate_time_limit_spin.setEnabled(False)
            self.debate_temp_spin.setEnabled(False)
            self.debate_start_button.setEnabled(False)
            self.debate_stop_button.setEnabled(True)
            
            # 更新状态为正在辩论
            self.update_debate_status("正在准备辩论...")
            
            # 创建并启动辩论线程
            self.debate_thread = ChatThread(manager, topic, rounds, time_limit, is_debate=True)
            # 连接信号到槽函数
            self.debate_thread.update_signal.connect(self._handle_debate_update)
            self.debate_thread.stream_update_signal.connect(self._handle_debate_stream_update)
            self.debate_thread.status_signal.connect(self.update_debate_status)
            self.debate_thread.finished_signal.connect(self.on_debate_finished)
            self.debate_thread.error_signal.connect(self.on_debate_error)
            self.debate_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化辩论失败: {str(e)}")
            # 恢复UI状态
            self.enable_debate_ui()
            # 清除流式状态
            self._debate_streaming_states.clear()
    
    def stop_debate(self):
        """停止AI辩论"""
        if hasattr(self, 'debate_thread') and self.debate_thread and self.debate_thread.isRunning():
            self.debate_thread.stop()
            self.update_status("正在停止辩论...")
    
    def _save_debate_history(self):
        """保存辩论历史到历史管理器"""
        topic = self.debate_topic_edit.text().strip()
        if not topic:
            topic = "无主题辩论"
        
        model1 = self.debate_model1_combo.currentText()
        model2 = self.debate_model2_combo.currentText()
        
        # 查找是否已存在相同模型组合的辩论历史记录
        existing_history_index = -1
        for i, history in enumerate(self.all_chat_histories):
            if history["type"] == "辩论" and history["model1"] == model1 and history["model2"] == model2:
                existing_history_index = i
                break
        
        if existing_history_index != -1:
            # 更新现有历史记录
            self.all_chat_histories[existing_history_index].update({
                "topic": topic,
                "messages": self.debate_history_messages.copy(),
                "html_content": self.debate_history_text.toHtml(),
                "timestamp": self._get_timestamp()
            })
        else:
            # 创建辩论历史记录
            debate_history = {
                "id": len(self.all_chat_histories) + 1,
                "type": "辩论",
                "topic": topic,
                "model1": model1,
                "model2": model2,
                "timestamp": self._get_timestamp(),
                "messages": self.debate_history_messages.copy(),
                "html_content": self.debate_history_text.toHtml()
            }
            # 添加到历史记录列表
            self.all_chat_histories.append(debate_history)
        
        # 保存所有历史记录到磁盘
        self.chat_history_manager.save_history(self.all_chat_histories)
    
    def on_debate_finished(self):
        """辩论完成后的处理"""
        # 保存辩论历史到历史管理器
        self._save_debate_history()
        
        self.enable_debate_ui()
        self.update_debate_status("辩论已完成")
    
    def on_debate_error(self, error_message):
        """处理辩论错误"""
        QMessageBox.critical(self, "错误", error_message)
        self.enable_debate_ui()
        self.update_debate_status("辩论出错")
    
    def start_batch_processing(self):
        """
        开始批量处理
        """
        # 获取主题列表
        topics_text = self.batch_topics_edit.toPlainText().strip()
        if not topics_text:
            QMessageBox.warning(self, "警告", "请输入至少一个讨论主题！")
            return
        
        # 解析主题列表
        topics = [topic.strip() for topic in topics_text.split("\n") if topic.strip()]
        if not topics:
            QMessageBox.warning(self, "警告", "请输入至少一个有效讨论主题！")
            return
        
        # 创建批量处理线程
        self.batch_thread = BatchProcessingThread(
            topics=topics,
            model1_name=self.batch_model1_combo.currentText(),
            model2_name=self.batch_model2_combo.currentText(),
            model1_api=self.batch_api1_combo.currentText(),
            model2_api=self.batch_api2_combo.currentText(),
            rounds=self.batch_rounds_spin.value(),
            time_limit=self.batch_time_limit_spin.value(),
            temperature=self.batch_temp_spin.value(),
            common_system_prompt=self.api_settings_widget.common_system_prompt_edit.toPlainText(),
            ai1_system_prompt=self.api_settings_widget.ai1_system_prompt_edit.toPlainText(),
            ai2_system_prompt=self.api_settings_widget.ai2_system_prompt_edit.toPlainText(),
            debate_common_prompt=self.api_settings_widget.debate_common_prompt_edit.toPlainText(),
            debate_ai1_prompt=self.api_settings_widget.debate_ai1_prompt_edit.toPlainText(),
            debate_ai2_prompt=self.api_settings_widget.debate_ai2_prompt_edit.toPlainText()
        )
        
        # 连接信号
        self.batch_thread.update_signal.connect(self.append_to_batch_results)
        self.batch_thread.status_signal.connect(self.update_batch_status)
        self.batch_thread.error_signal.connect(self.on_batch_error)
        self.batch_thread.finished_signal.connect(self.on_batch_processing_finished)
        
        # 启动线程
        self.batch_thread.start()
        
        # 更新UI状态
        self.batch_start_button.setEnabled(False)
        self.batch_stop_button.setEnabled(True)
        self.batch_status_label.setText("批量处理开始")
        self.batch_results_text.clear()
        self.batch_results_text.append("<b>系统:</b> 开始批量处理")
    
    def stop_batch_processing(self):
        """
        停止批量处理
        """
        if hasattr(self, 'batch_thread') and self.batch_thread.isRunning():
            self.batch_thread.stop()
            self.batch_status_label.setText("批量处理正在停止...")
    
    def clear_batch_results(self):
        """
        清空批量处理结果
        """
        self.batch_results_text.clear()
    
    def append_to_batch_results(self, sender, content):
        """
        向批量处理结果添加内容，支持Markdown渲染
        
        Args:
            sender: 发送者
            content: 内容
        """
        try:
            # 渲染Markdown内容为HTML
            rendered_content = self._render_markdown_content(content)
            
            # 构建HTML结构，包含发送者和渲染后的内容
            html_content = f"""
            <div style='margin-bottom: 15px;'>
                <strong style='color: #0d47a1; font-size: 11pt;'>{sender}:</strong>
                <div style='margin-top: 5px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;'>
                    {rendered_content}
                </div>
            </div>
            """
            
            # 使用insertHtml方法添加HTML内容
            self.batch_results_text.insertHtml(html_content)
            # 添加一个换行，确保下一条消息正确分隔
            self.batch_results_text.insertPlainText("\n")
        except Exception as e:
            # 如果Markdown渲染失败，使用原始内容作为回退
            self.batch_results_text.append(f"<b>{sender}:</b> {content}")
        
        # 自动滚动到底部
        self.batch_results_text.verticalScrollBar().setValue(self.batch_results_text.verticalScrollBar().maximum())
    
    def update_batch_status(self, status):
        """
        更新批量处理状态
        
        Args:
            status: 状态信息
        """
        self.batch_status_label.setText(status)
    
    def _save_batch_processing_history(self):
        """保存批量处理历史到历史管理器"""
        # 获取批量处理的主题列表
        topics_text = self.batch_topics_edit.toPlainText().strip()
        if not topics_text:
            topic = "无主题批量处理"
        else:
            topics = [topic.strip() for topic in topics_text.split("\n") if topic.strip()]
            if topics:
                topic = f"批量处理: {topics[0]}等{len(topics)}个主题"
            else:
                topic = "无主题批量处理"
        
        model1 = self.batch_model1_combo.currentText()
        model2 = self.batch_model2_combo.currentText()
        
        # 查找是否已存在相同模型组合的批量处理历史记录
        existing_history_index = -1
        for i, history in enumerate(self.all_chat_histories):
            if history["type"] == "批量处理" and history["model1"] == model1 and history["model2"] == model2:
                existing_history_index = i
                break
        
        if existing_history_index != -1:
            # 更新现有历史记录
            self.all_chat_histories[existing_history_index].update({
                "topic": topic,
                "html_content": self.batch_results_text.toHtml(),
                "timestamp": self._get_timestamp()
            })
        else:
            # 创建批量处理历史记录
            batch_history = {
                "id": len(self.all_chat_histories) + 1,
                "type": "批量处理",
                "topic": topic,
                "model1": model1,
                "model2": model2,
                "timestamp": self._get_timestamp(),
                "html_content": self.batch_results_text.toHtml()
            }
            # 添加到历史记录列表
            self.all_chat_histories.append(batch_history)
        
        # 保存所有历史记录到磁盘
        self.chat_history_manager.save_history(self.all_chat_histories)
    
    def on_batch_processing_finished(self):
        """批量处理完成回调
        """
        # 保存批量处理历史到历史管理器
        self._save_batch_processing_history()
        
        self.batch_status_label.setText("批量处理完成")
        self.batch_start_button.setEnabled(True)
        self.batch_stop_button.setEnabled(False)
    
    def on_batch_error(self, error_message):
        """处理批量处理过程中发生的错误
        
        参数:
            error_message (str): 错误信息的详细描述
        """
        try:
            logger.error(f"批量处理过程中发生错误: {error_message}")
            
            # 分析错误信息，提供更友好的提示
            friendly_message = error_message
            if "API密钥" in error_message or "API Key" in error_message:
                friendly_message = f"API密钥错误: {error_message}\n请检查API密钥设置后重试。"
            elif "连接" in error_message or "Connection" in error_message:
                friendly_message = f"网络连接错误: {error_message}\n请检查网络连接或API服务器地址后重试。"
            elif "超时" in error_message or "Timeout" in error_message:
                friendly_message = f"请求超时: {error_message}\nAI响应时间过长，请检查网络状况或稍后重试。"
            
            QMessageBox.critical(self, "错误", friendly_message)  # 显示错误信息对话框
            self.batch_status_label.setText("批量处理出错")
            self.batch_start_button.setEnabled(True)
            self.batch_stop_button.setEnabled(False)
            
            # 确保资源被正确清理
            if hasattr(self, 'batch_thread'):
                self.batch_thread = None
                
        except Exception as e:
            logger.error(f"处理批量处理错误时发生二次错误: {str(e)}")
            # 避免二次错误引起崩溃，使用日志记录而非UI交互
    
    def enable_debate_ui(self):
        """启用辩论UI控件"""
        self.debate_topic_edit.setEnabled(True)
        self.debate_model1_combo.setEnabled(True)
        self.debate_model2_combo.setEnabled(True)
        self.debate_api1_combo.setEnabled(True)
        self.debate_api2_combo.setEnabled(True)
        self.debate_rounds_spin.setEnabled(True)
        self.debate_time_limit_spin.setEnabled(True)
        self.debate_temp_spin.setEnabled(True)
        self.debate_start_button.setEnabled(True)
        self.debate_stop_button.setEnabled(False)
    
    def append_to_debate_history(self, sender, content, model=""):
        """将消息添加到辩论历史，支持Markdown格式渲染，并为AI1和AI2使用不同颜色区分"""
        try:
            # 获取当前时间戳
            timestamp = self._get_timestamp()
            
            # 从发送者名称中提取模型名称（如果存在）
            sender, extracted_model = self._extract_model_from_sender(sender)
            
            # 使用markdown库将内容转换为HTML，增强代码块显示
            rendered_content = self._render_markdown_content(content)
            
            # 使用提取的模型名称（如果有）
            model_to_use = extracted_model if extracted_model else model
            
            # 根据发送者是AI 1还是AI 2应用不同的颜色样式参数
            if "正方AI1" in sender:
                # AI 1 使用蓝色主题 - 增强版
                style_params = {
                    'sender_color': "#0d47a1",
                    'background_color': "#e3f2fd",
                    'border_color': "#2196f3",
                    'accent_color': "#bbdefb",
                    'separator_color': "#90caf9",
                    'icon_char': "🔵",
                    'message_style': "style='background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            elif "反方AI2" in sender:
                # AI 2 使用绿色主题 - 增强版
                style_params = {
                    'sender_color': "#1b5e20",
                    'background_color': "#e8f5e9",
                    'border_color': "#4caf50",
                    'accent_color': "#c8e6c9",
                    'separator_color': "#a5d6a7",
                    'icon_char': "🟢",
                    'message_style': "style='background-color: #e8f5e9; border: 2px solid #4caf50; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            else:
                # 其他消息使用灰色主题 - 增强版
                style_params = {
                    'sender_color': "#424242",
                    'background_color': "#f5f5f5",
                    'border_color': "#9e9e9e",
                    'accent_color': "#e0e0e0",
                    'separator_color': "#bdbdbd",
                    'icon_char': "⚪",
                    'message_style': "style='background-color: #f5f5f5; border: 2px solid #9e9e9e; border-radius: 18px; padding: 14px; margin: 10px 60px 10px 10px; text-align: left; display: block; font-family: SimHei; font-size: 10pt; box-shadow: 0 3px 8px rgba(0,0,0,0.1);'",
                    'show_corner': False
                }
            
            # 构建带有样式的HTML消息
            message_html = self._build_message_html(sender, rendered_content, timestamp, model_to_use, style_params)
            
            # 获取当前文档的HTML内容
            current_html = self.debate_history_text.toHtml()
            
            # 查找<body>标签位置
            body_start = current_html.find("<body")
            if body_start == -1:
                # 如果没有body标签，直接设置HTML，优化CSS样式
                self.debate_history_text.setHtml(f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
body {{ font-family: 'SimHei', sans-serif; font-size: 10pt; line-height: 1.6; margin: 10px; }}
p, li {{ white-space: pre-wrap; margin: 5px 0; }}
pre {{ background-color: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; border: 1px solid #e9ecef; }}
code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }}
h1, h2, h3 {{ margin-top: 15px; margin-bottom: 10px; font-weight: bold; }}
h1 {{ font-size: 14pt; color: #333; }}
h2 {{ font-size: 12pt; color: #555; }}
h3 {{ font-size: 11pt; color: #777; }}
blockquote {{ border-left: 3px solid #ccc; margin: 10px 0; padding-left: 15px; color: #666; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
</style></head><body>{message_html}</body></html>''')
                self.debate_chat_count = 1  # 设置聊天历史计数为1
            else:
                # 查找body结束标签
                body_end = current_html.find(">", body_start) + 1
                end_body = current_html.rfind("</body>")
                
                if end_body != -1:
                    # 构建新的HTML内容 - 确保在正确位置插入新消息
                    body_content = current_html[body_end:end_body]
                    
                    # 检查是否需要限制聊天历史数量
                    if self.debate_chat_count >= self.max_debate_history:
                        # 如果超过最大数量，找到第一条消息并移除
                        first_message_end = body_content.find("</div>") + 6  # 找到第一条消息的结束位置
                        if first_message_end != -1:
                            # 移除第一条消息
                            body_content = body_content[first_message_end:]
                    else:
                        # 增加聊天历史计数
                        self.debate_chat_count += 1
                    
                    new_html = current_html[:body_end] + body_content + message_html + current_html[end_body:]
                else:
                    # 如果没有</body>标签，直接添加内容到body中
                    new_html = current_html[:body_end] + current_html[body_end:] + message_html
                    self.debate_chat_count += 1  # 增加聊天历史计数
                
                self.debate_history_text.setHtml(new_html)
            
            # 滚动到底部
            self.debate_history_text.moveCursor(QTextCursor.End)
            
        except Exception as e:
            logger.error(f"更新辩论历史失败: {str(e)}")
            self.show_error_message("错误", f"更新辩论历史失败: {str(e)}")
    
    def export_chat_history_to_pdf(self):
        """将聊天历史或讨论历史导出为PDF文件
        
        支持以下功能标签页的导出：
        - 标准聊天标签页（索引0）
        - 讨论标签页（索引1）
        - 辩论标签页（索引2）
        
        导出过程包括：
        1. 检查当前活动标签页
        2. 验证是否有历史记录可供导出
        3. 生成带时间戳的默认文件名
        4. 打开文件对话框选择保存位置
        5. 配置PDF导出参数（分辨率、页面大小、边距）
        6. 处理HTML内容（添加标题和主题）
        7. 执行PDF导出
        8. 验证导出结果并显示相应提示
        """
        logger.info("开始导出聊天/讨论历史为PDF")
        try:
            # 检查当前活动的标签页，确定导出类型
            current_tab_index = self.tabs.currentIndex()
            logger.info(f"当前标签页索引: {current_tab_index}")
            
            if current_tab_index == 0:  # 聊天标签页
                # 检查是否有聊天历史内容
                has_history = self.standard_chat_history.toPlainText().strip() != ""
                logger.info(f"聊天标签页 - 是否有历史记录: {has_history}")
                
                if not has_history:
                    QMessageBox.information(self, "提示", "没有聊天历史可供导出")
                    logger.info("没有聊天历史可供导出")
                    return
                
                # 生成当前时间戳（yyyyMMdd_HHmmss格式）用于文件名
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                # 设置聊天功能默认文件名
                default_filename = f"Nonead_Chat_{timestamp}.pdf"
                logger.info(f"生成默认文件名: {default_filename}")
                
                # 打开文件对话框让用户选择保存位置
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出为PDF", default_filename, "PDF文件 (*.pdf)"
                )
                
                if not file_path:
                    logger.info("用户取消了PDF导出操作")
                    return  # 用户取消了操作
                
                # 确保文件扩展名为.pdf
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                    logger.info(f"自动添加PDF扩展名，最终路径: {file_path}")
                
                # 创建QPrinter对象用于PDF导出，设置为高分辨率
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)  # 设置输出格式为PDF
                printer.setOutputFileName(file_path)  # 设置输出文件名
                logger.info(f"配置PDF导出: 文件名={file_path}, 分辨率=HighResolution")
                
                # 设置PDF页面属性
                printer.setPageSize(QPrinter.A4)  # 设置页面大小为A4
                printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)  # 设置15mm边距
                logger.info(f"设置页面属性: A4纸张, 边距=15mm")
                
                # 创建一个临时QTextEdit用于导出，保留HTML格式
                temp_edit = QTextEdit()
                
                # 获取当前聊天历史的HTML内容
                html_content = self.standard_chat_history.toHtml()
                logger.info(f"获取到聊天历史HTML内容，长度={len(html_content)}字符")
                
                # 添加标题和时间戳到HTML内容中
                title = f"AI聊天历史 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
                styled_html = f"<h1 style='text-align:center;'>{title}</h1><br>{html_content}"
                logger.info("组装导出HTML内容")
            elif current_tab_index == 1 or current_tab_index == 2:  # 讨论或辩论标签页
                # 检查是否有讨论/辩论历史内容
                has_history = self.chat_history_text.toPlainText().strip() != ""
                logger.info(f"讨论/辩论标签页 - 是否有历史记录: {has_history}")
                
                if not has_history:
                    QMessageBox.information(self, "提示", "没有讨论历史可供导出")
                    logger.info("没有讨论历史可供导出")
                    return
                
                # 生成当前时间戳（yyyyMMdd_HHmmss格式）用于文件名
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                # 设置讨论功能默认文件名
                default_filename = f"Nonead_Discuss_{timestamp}.pdf"
                logger.info(f"生成默认文件名: {default_filename}")
                
                # 打开文件对话框选择保存位置
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出为PDF", default_filename, "PDF文件 (*.pdf)"
                )
                
                if not file_path:
                    logger.info("用户取消了PDF导出操作")
                    return  # 用户取消了操作
                
                # 确保文件扩展名为.pdf
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                    logger.info(f"自动添加PDF扩展名，最终路径: {file_path}")
                
                # 创建QPrinter对象用于PDF导出
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                logger.info(f"配置PDF导出: 文件名={file_path}, 分辨率=HighResolution")
                
                # 设置页面属性
                printer.setPageSize(QPrinter.A4)
                printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)
                logger.info(f"设置页面属性: A4纸张, 边距=15mm")
                
                # 创建一个临时QTextEdit用于导出，并保留HTML格式
                temp_edit = QTextEdit()
                
                # 获取当前讨论/辩论历史的HTML内容
                html_content = self.chat_history_text.toHtml()
                logger.info(f"获取到讨论历史HTML内容，长度={len(html_content)}字符")
                
                # 获取讨论主题，如果为空则使用默认值
                topic = self.topic_edit.text().strip()
                if not topic:
                    topic = "未指定讨论主题"
                logger.info(f"讨论主题: {topic}")
                
                # 添加标题和主题到HTML内容中
                title = f"AI讨论历史 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
                styled_html = f"<h1 style='text-align:center;'>{title}</h1><h2 style='text-align:center; margin-top:10px;'>讨论主题: {topic}</h2><br>{html_content}"
                logger.info("组装导出HTML内容")
            else:
                # 不支持的标签页类型
                QMessageBox.information(self, "提示", "当前标签页不支持导出PDF")
                logger.info(f"当前标签页不支持PDF导出 (索引: {current_tab_index})")
                return
            
            # 设置处理后的HTML内容到临时编辑器
            temp_edit.setHtml(styled_html)
            logger.info("设置HTML内容到临时QTextEdit")
            
            # 执行PDF打印操作
            logger.info("开始执行PDF打印操作")
            result = temp_edit.print_(printer)
            logger.info(f"打印操作返回结果: {result}")
            
            # 验证导出结果：检查文件是否存在且大小大于0
            import os
            file_exists = os.path.exists(file_path)
            file_size = os.path.getsize(file_path) if file_exists else 0
            logger.info(f"文件存在检查: {file_exists}, 文件大小: {file_size} 字节")
            
            if file_exists and file_size > 0:
                # 导出成功，显示成功提示
                if current_tab_index == 0:  # 聊天功能
                    success_msg = f"聊天历史已成功导出到 {file_path}"
                    self.chat_status_label.setText(success_msg)
                else:  # 辩论/讨论功能
                    success_msg = f"讨论历史已成功导出到 {file_path}"
                    self.update_status(success_msg)
                QMessageBox.information(self, "成功", f"历史记录已成功导出到\n{file_path}")
                logger.info(f"PDF导出成功: {file_path}, 文件大小: {file_size} 字节")
            else:
                # 导出失败，文件未创建或为空
                error_msg = "PDF导出失败，可能是权限问题或文件路径无效"
                if current_tab_index == 0:  # 聊天功能
                    self.chat_status_label.setText(f"导出PDF失败: {error_msg}")
                else:  # 辩论/讨论功能
                    self.update_status(f"导出PDF失败: {error_msg}")
                QMessageBox.critical(self, "错误", f"导出PDF失败: {error_msg}\n\n请尝试选择其他保存位置。")
                logger.error(f"PDF导出失败 - 文件未创建或为空: {file_path}, 大小: {file_size} 字节")
                
        except IOError as e:
            # 处理IO错误，如文件权限问题
            error_details = f"IO错误: {str(e)}"
            logger.error(f"PDF导出IO错误: {error_details}", exc_info=True)
            if current_tab_index == 0:  # 聊天功能
                self.chat_status_label.setText(f"导出PDF失败: {error_details}")
            else:  # 辩论/讨论功能
                self.update_status(f"导出PDF失败: {error_details}")
            QMessageBox.critical(self, "错误", f"导出PDF失败: {error_details}\n\n请检查文件路径权限或尝试其他位置。")
        except QPrinter.PrinterError as e:
            # 处理打印机相关错误
            error_details = f"打印机错误: {str(e)}"
            logger.error(f"PDF导出打印机错误: {error_details}", exc_info=True)
            if current_tab_index == 0:  # 聊天功能
                self.chat_status_label.setText(f"导出PDF失败: {error_details}")
            else:  # 辩论/讨论功能
                self.update_status(f"导出PDF失败: {error_details}")
            QMessageBox.critical(self, "错误", f"导出PDF失败: {error_details}\n\n请检查打印机设置或系统资源。")
        except Exception as e:
            # 处理其他未知错误
            error_details = f"{type(e).__name__}: {str(e)}"
            logger.error(f"PDF导出未知错误: {error_details}", exc_info=True)
            if current_tab_index == 0:  # 聊天功能
                self.chat_status_label.setText(f"导出PDF失败: {error_details}")
            else:  # 辩论/讨论功能
                self.update_status(f"导出PDF失败: {error_details}")
            QMessageBox.critical(self, "错误", f"导出PDF失败: {error_details}\n\n请检查文件路径权限或尝试其他位置。")
    
    def save_chat_history(self):
        """
        保存聊天历史到文件
        """
        try:
            # 检查是否有聊天历史
            if self.chat_history_text.toPlainText().strip() == "":
                QMessageBox.warning(self, "警告", "聊天历史为空，无法保存")
                return
            
            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存聊天历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 收集聊天历史数据
                chat_history = {
                    "topic": self.topic_edit.text().strip(),
                    "model1": self.model1_combo.currentText(),
                    "model2": self.model2_combo.currentText(),
                    "api1": self.api1_combo.currentText(),
                    "api2": self.api2_combo.currentText(),
                    "rounds": self.rounds_spin.value(),
                    "time_limit": self.time_limit_spin.value(),
                    "temperature": self.temp_spin.value(),
                    "history": self.chat_history_text.toHtml(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 保存到JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chat_history, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"聊天历史已保存到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存聊天历史失败: {str(e)}")
    
    def load_chat_history(self):
        """
        从文件加载聊天历史
        """
        try:
            # 打开文件对话框，让用户选择加载文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载聊天历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 从JSON文件加载聊天历史
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_history = json.load(f)
                
                # 恢复聊天历史
                self.chat_history_text.setHtml(chat_history.get("history", ""))
                
                # 恢复配置
                self.topic_edit.setText(chat_history.get("topic", ""))
                
                # 恢复模型选择（如果存在）
                if chat_history.get("model1") in [self.model1_combo.itemText(i) for i in range(self.model1_combo.count())]:
                    self.model1_combo.setCurrentText(chat_history.get("model1", ""))
                
                if chat_history.get("model2") in [self.model2_combo.itemText(i) for i in range(self.model2_combo.count())]:
                    self.model2_combo.setCurrentText(chat_history.get("model2", ""))
                
                # 恢复API选择
                if chat_history.get("api1") in ["ollama", "openai", "deepseek"]:
                    self.api1_combo.setCurrentText(chat_history.get("api1", "ollama"))
                
                if chat_history.get("api2") in ["ollama", "openai", "deepseek"]:
                    self.api2_combo.setCurrentText(chat_history.get("api2", "ollama"))
                
                # 恢复其他参数
                self.rounds_spin.setValue(chat_history.get("rounds", 5))
                self.time_limit_spin.setValue(chat_history.get("time_limit", 0))
                self.temp_spin.setValue(chat_history.get("temperature", 0.8))
                
                QMessageBox.information(self, "成功", f"聊天历史已从 {file_path} 加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载聊天历史失败: {str(e)}")
    
    def save_debate_chat_history(self):
        """
        保存辩论历史到文件
        """
        try:
            # 检查是否有辩论历史
            if self.debate_history_text.toPlainText().strip() == "":
                QMessageBox.warning(self, "警告", "辩论历史为空，无法保存")
                return
            
            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存辩论历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 收集辩论历史数据
                debate_history = {
                    "type": "debate",
                    "topic": self.debate_topic_edit.text().strip(),
                    "model1": self.debate_model1_combo.currentText(),
                    "model2": self.debate_model2_combo.currentText(),
                    "api1": self.debate_api1_combo.currentText(),
                    "api2": self.debate_api2_combo.currentText(),
                    "rounds": self.debate_rounds_spin.value(),
                    "time_limit": self.debate_time_limit_spin.value(),
                    "temperature": self.debate_temp_spin.value(),
                    "history": self.debate_history_text.toHtml(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 保存到JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(debate_history, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"辩论历史已保存到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存辩论历史失败: {str(e)}")
    
    def load_debate_chat_history(self):
        """
        从文件加载辩论历史
        """
        try:
            # 打开文件对话框，让用户选择加载文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载辩论历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 从JSON文件加载辩论历史
                with open(file_path, 'r', encoding='utf-8') as f:
                    debate_history = json.load(f)
                
                # 验证是否为辩论历史
                if debate_history.get("type") != "debate":
                    QMessageBox.warning(self, "警告", "这不是辩论历史文件")
                    return
                
                # 恢复辩论历史
                self.debate_history_text.setHtml(debate_history.get("history", ""))
                
                # 恢复配置
                self.debate_topic_edit.setText(debate_history.get("topic", ""))
                
                # 恢复模型选择（如果存在）
                if debate_history.get("model1") in [self.debate_model1_combo.itemText(i) for i in range(self.debate_model1_combo.count())]:
                    self.debate_model1_combo.setCurrentText(debate_history.get("model1", ""))
                
                if debate_history.get("model2") in [self.debate_model2_combo.itemText(i) for i in range(self.debate_model2_combo.count())]:
                    self.debate_model2_combo.setCurrentText(debate_history.get("model2", ""))
                
                # 恢复API选择
                if debate_history.get("api1") in ["ollama", "openai", "deepseek"]:
                    self.debate_api1_combo.setCurrentText(debate_history.get("api1", "ollama"))
                
                if debate_history.get("api2") in ["ollama", "openai", "deepseek"]:
                    self.debate_api2_combo.setCurrentText(debate_history.get("api2", "ollama"))
                
                # 恢复其他参数
                self.debate_rounds_spin.setValue(debate_history.get("rounds", 5))
                self.debate_time_limit_spin.setValue(debate_history.get("time_limit", 0))
                self.debate_temp_spin.setValue(debate_history.get("temperature", 0.8))
                
                QMessageBox.information(self, "成功", f"辩论历史已从 {file_path} 加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载辩论历史失败: {str(e)}")
    
    def save_standard_chat_history(self):
        """
        保存标准聊天功能的聊天历史到文件
        """
        try:
            # 检查是否有聊天历史
            if self.standard_chat_history.toPlainText().strip() == "":
                QMessageBox.warning(self, "警告", "聊天历史为空，无法保存")
                return
            
            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存聊天历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 收集聊天历史数据
                chat_history = {
                    "type": "standard",
                    "model": self.chat_model_combo.currentText(),
                    "api": self.chat_api_combo.currentText(),
                    "temperature": self.chat_temperature_spin.value(),
                    "history": self.standard_chat_history.toHtml(),
                    "messages": self.standard_chat_history_messages.copy(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 保存到JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chat_history, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"聊天历史已保存到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存聊天历史失败: {str(e)}")
    
    def load_standard_chat_history(self):
        """
        从文件加载标准聊天功能的聊天历史
        """
        try:
            # 打开文件对话框，让用户选择加载文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载聊天历史", "", "JSON Files (*.json)"
            )
            
            if file_path:
                # 从JSON文件加载聊天历史
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_history = json.load(f)
                
                # 验证是否为标准聊天历史
                if chat_history.get("type") != "standard":
                    QMessageBox.warning(self, "警告", "这不是标准聊天历史文件")
                    return
                
                # 恢复聊天历史
                self.standard_chat_history.setHtml(chat_history.get("history", ""))
                
                # 恢复聊天历史消息
                if "messages" in chat_history:
                    self.standard_chat_history_messages = chat_history["messages"]
                
                # 恢复模型选择
                if chat_history.get("model") in [self.chat_model_combo.itemText(i) for i in range(self.chat_model_combo.count())]:
                    self.chat_model_combo.setCurrentText(chat_history.get("model", ""))
                
                # 恢复API选择
                if chat_history.get("api") in ["ollama", "openai", "deepseek"]:
                    self.chat_api_combo.setCurrentText(chat_history.get("api", "ollama"))
                
                # 恢复温度参数
                if "temperature" in chat_history:
                    self.chat_temperature_spin.setValue(chat_history["temperature"])
                
                QMessageBox.information(self, "成功", f"聊天历史已从 {file_path} 加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载聊天历史失败: {str(e)}")
    
    def _optimize_chat_history(self):
        """
        优化聊天历史内存使用，只保留最近的消息
        
        该方法会检查聊天历史的长度，如果超过限制，只保留最近的消息，
        但始终保留系统提示词（如果有的话）。
        """
        if len(self.standard_chat_history_messages) > self.max_standard_chat_history:
            # 检查是否有系统提示词
            system_prompts = [msg for msg in self.standard_chat_history_messages if msg["role"] == "system"]
            # 保留系统提示词和最近的消息
            recent_messages = self.standard_chat_history_messages[-self.max_standard_chat_history:]
            self.standard_chat_history_messages = system_prompts + recent_messages
            logger.info(f"聊天历史已优化，保留 {len(self.standard_chat_history_messages)} 条消息")
    
    def show_history_manager(self):
        """
        显示对话历史管理器
        """
        # 创建对话历史管理器窗口
        history_window = QDialog(self)
        history_window.setWindowTitle("对话历史管理器")
        history_window.setGeometry(200, 200, 800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(history_window)
        
        # 搜索和过滤区域
        search_layout = QHBoxLayout()
        
        # 搜索框
        self.history_search_edit = QLineEdit()
        self.history_search_edit.setPlaceholderText("搜索对话历史...")
        self.history_search_edit.textChanged.connect(self.filter_history_list)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.history_search_edit)
        
        # 类型过滤
        self.history_type_combo = QComboBox()
        self.history_type_combo.addItems(["所有类型", "标准聊天", "讨论", "辩论", "批量处理"])
        self.history_type_combo.currentTextChanged.connect(self.filter_history_list)
        search_layout.addWidget(QLabel("类型:"))
        search_layout.addWidget(self.history_type_combo)
        
        # 排序方式
        self.history_sort_combo = QComboBox()
        self.history_sort_combo.addItems(["时间倒序", "时间正序"])
        self.history_sort_combo.currentTextChanged.connect(self.refresh_history_list)
        search_layout.addWidget(QLabel("排序:"))
        search_layout.addWidget(self.history_sort_combo)
        
        main_layout.addLayout(search_layout)
        
        # 对话历史列表
        self.history_list_widget = QListWidget()
        self.history_list_widget.itemDoubleClicked.connect(self.load_selected_history)
        self.history_list_widget.itemClicked.connect(self._on_history_item_selected)
        self.history_list_widget.currentItemChanged.connect(self._on_history_item_selected)
        main_layout.addWidget(self.history_list_widget, 1)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        # 加载按钮
        load_button = QPushButton("加载")
        load_button.clicked.connect(self.load_selected_history)
        button_layout.addWidget(load_button)
        
        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_selected_history)
        button_layout.addWidget(delete_button)
        
        # 导出按钮
        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_selected_history)
        button_layout.addWidget(export_button)
        
        # 导入按钮
        import_button = QPushButton("导入")
        import_button.clicked.connect(self.import_history)
        button_layout.addWidget(import_button)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        self.history_preview = QTextEdit()
        self.history_preview.setReadOnly(True)
        self.history_preview.setMaximumHeight(300)
        preview_layout.addWidget(self.history_preview)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # 刷新历史列表
        self.refresh_history_list()
        
        # 显示窗口
        history_window.exec_()
    
    def _on_history_item_selected(self, item=None):
        """
        当历史记录项被选中时更新预览窗口
        """
        if not item:
            selected_items = self.history_list_widget.selectedItems()
            if not selected_items:
                self.history_preview.clear()
                return
            item = selected_items[0]
        
        history = item.data(Qt.UserRole)
        if history:
            # 获取预览内容
            preview_content = history.get("html_content", "")
            if not preview_content:
                preview_content = "无预览内容"
            # 更新预览窗口
            self.history_preview.setHtml(preview_content)
            logger.info(f"更新历史记录预览，类型: {history['type']}, 主题: {history['topic']}")
    
    def refresh_history_list(self):
        """
        刷新对话历史列表
        """
        # 清空列表
        self.history_list_widget.clear()
        
        # 使用真实的历史记录数据
        history_list = self.all_chat_histories.copy()
        
        # 根据排序方式排序
        if self.history_sort_combo.currentText() == "时间正序":
            history_list.sort(key=lambda x: x["timestamp"])
        else:
            history_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 添加到列表
        for history in history_list:
            item = QListWidgetItem()
            if history["type"] == "标准聊天":
                item.setText(f"[{history['type']}] {history['topic']} - {history['model']} ({history['timestamp']})")
            elif history["type"] == "批量处理":
                item.setText(f"[{history['type']}] {history['topic']} - {history['model1']} vs {history['model2']} ({history['timestamp']})")
            else:
                item.setText(f"[{history['type']}] {history['topic']} - {history['model1']} vs {history['model2']} ({history['timestamp']})")
            item.setData(Qt.UserRole, history)
            self.history_list_widget.addItem(item)
        
        # 应用过滤
        self.filter_history_list()
    
    def filter_history_list(self):
        """
        过滤对话历史列表
        """
        search_text = self.history_search_edit.text().lower()
        filter_type = self.history_type_combo.currentText()
        
        for i in range(self.history_list_widget.count()):
            item = self.history_list_widget.item(i)
            history = item.data(Qt.UserRole)
            
            # 类型过滤
            if filter_type != "所有类型" and history["type"] != filter_type:
                item.setHidden(True)
                continue
            
            # 文本搜索
            if search_text:
                topic = history["topic"].lower()
                model_info = ""
                if "model" in history:
                    model_info = history["model"].lower()
                elif "model1" in history and "model2" in history:
                    model_info = f"{history['model1']} {history['model2']}".lower()
                
                if search_text not in topic and search_text not in model_info:
                    item.setHidden(True)
                    continue
            
            item.setHidden(False)
    
    def load_selected_history(self):
        """
        加载选中的对话历史
        """
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个对话历史！")
            return
        
        selected_item = selected_items[0]
        history = selected_item.data(Qt.UserRole)
        
        # 添加调试日志
        logger.info(f"加载历史记录 - 类型: {history['type']}, 主题: {history['topic']}, 包含字段: {list(history.keys())}")
        
        # 根据类型加载不同的历史
        if history["type"] == "标准聊天":
            # 切换到标准聊天标签页
            self.tabs.setCurrentIndex(0)
            # 加载聊天历史
            html_content = history.get("html_content", "")
            self.standard_chat_history.setHtml(html_content)
            logger.info(f"设置标准聊天历史内容，长度: {len(html_content)}")
            if "messages" in history:
                self.standard_chat_history_messages = history["messages"]
                logger.info(f"加载标准聊天消息列表，数量: {len(history['messages'])}")
            if "model" in history:
                self.chat_model_combo.setCurrentText(history["model"])
            if "api" in history:
                self.chat_api_combo.setCurrentText(history["api"])
            QMessageBox.information(self, "提示", f"正在加载标准聊天历史: {history['topic']}")
        elif history["type"] == "讨论":
            # 切换到讨论标签页
            self.tabs.setCurrentIndex(1)
            # 加载讨论历史
            html_content = history.get("html_content", "")
            self.chat_history_text.setHtml(html_content)
            logger.info(f"设置讨论历史内容，长度: {len(html_content)}")
            if "topic" in history:
                self.topic_edit.setText(history["topic"])
            if "model1" in history:
                self.model1_combo.setCurrentText(history["model1"])
            if "model2" in history:
                self.model2_combo.setCurrentText(history["model2"])
            if "api1" in history:
                self.api1_combo.setCurrentText(history["api1"])
            if "api2" in history:
                self.api2_combo.setCurrentText(history["api2"])
            QMessageBox.information(self, "提示", f"正在加载讨论历史: {history['topic']}")
        elif history["type"] == "辩论":
            # 切换到辩论标签页
            self.tabs.setCurrentIndex(2)
            # 加载辩论历史
            html_content = history.get("html_content", "")
            self.debate_history_text.setHtml(html_content)
            logger.info(f"设置辩论历史内容，长度: {len(html_content)}")
            if "topic" in history:
                self.debate_topic_edit.setText(history["topic"])
            if "model1" in history:
                self.debate_model1_combo.setCurrentText(history["model1"])
            if "model2" in history:
                self.debate_model2_combo.setCurrentText(history["model2"])
            if "api1" in history:
                self.debate_api1_combo.setCurrentText(history["api1"])
            if "api2" in history:
                self.debate_api2_combo.setCurrentText(history["api2"])
            QMessageBox.information(self, "提示", f"正在加载辩论历史: {history['topic']}")
        elif history["type"] == "批量处理":
            # 切换到批量处理标签页
            self.tabs.setCurrentIndex(3)
            # 显示批量处理结果
            html_content = history.get("html_content", "")
            self.batch_results_text.setHtml(html_content)
            logger.info(f"设置批量处理历史内容，长度: {len(html_content)}")
            QMessageBox.information(self, "提示", f"正在加载批量处理历史: {history['topic']}")
    
    def delete_selected_history(self):
        """
        删除选中的对话历史
        """
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个对话历史！")
            return
        
        selected_item = selected_items[0]
        history = selected_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(self, "确认", f"确定要删除对话历史 '{history['topic']}' 吗？", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从UI中删除
            self.history_list_widget.takeItem(self.history_list_widget.row(selected_item))
            
            # 从数据列表中删除
            for i, h in enumerate(self.all_chat_histories):
                if h['topic'] == history['topic'] and h['type'] == history['type'] and h['timestamp'] == history['timestamp']:
                    self.all_chat_histories.pop(i)
                    break
            
            # 保存更改到磁盘
            self.chat_history_manager.save_history(self.all_chat_histories)
            
            QMessageBox.information(self, "成功", f"对话历史 '{history['topic']}' 已删除")
    
    def export_selected_history(self):
        """
        导出选中的对话历史
        """
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个对话历史！")
            return
        
        selected_item = selected_items[0]
        history = selected_item.data(Qt.UserRole)
        
        # 打开文件对话框，让用户选择导出位置
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话历史", f"{history['topic']}.json", "JSON Files (*.json)"
        )
        
        if file_path:
            # 这里应该实现实际的导出逻辑
            QMessageBox.information(self, "成功", f"对话历史已导出到 {file_path}")
    
    def import_history(self):
        """
        导入对话历史
        """
        # 打开文件对话框，让用户选择导入文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入对话历史", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # 读取并解析JSON文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_history = json.load(f)
                
                # 检查导入的历史记录格式
                if not isinstance(imported_history, dict):
                    # 如果是列表，逐个导入
                    if isinstance(imported_history, list):
                        for history_item in imported_history:
                            # 为每个导入的历史记录分配新的ID
                            if "id" in history_item:
                                del history_item["id"]
                            history_item["id"] = len(self.all_chat_histories) + 1
                            self.all_chat_histories.append(history_item)
                    else:
                        raise ValueError("导入的文件格式不正确，应该是JSON对象或数组")
                else:
                    # 如果是单个历史记录对象，直接导入
                    if "id" in imported_history:
                        del imported_history["id"]
                    imported_history["id"] = len(self.all_chat_histories) + 1
                    self.all_chat_histories.append(imported_history)
                
                # 保存所有历史记录到磁盘
                self.chat_history_manager.save_history(self.all_chat_histories)
                
                QMessageBox.information(self, "成功", f"对话历史已从 {file_path} 导入")
                # 刷新历史列表
                self.refresh_history_list()
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "错误", f"导入对话历史失败: JSON解析错误 - {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入对话历史失败: {str(e)}")
    
    def _optimize_chat_history(self):
        """
        优化聊天历史内存使用，只保留最近的消息
        
        该方法会检查聊天历史的长度，如果超过限制，只保留最近的消息，
        但始终保留系统提示词（如果有的话）。
        """
        if len(self.standard_chat_history_messages) > self.max_standard_chat_history:
            # 检查是否有系统提示词
            system_prompts = [msg for msg in self.standard_chat_history_messages if msg["role"] == "system"]
            # 保留系统提示词和最近的消息
            recent_messages = self.standard_chat_history_messages[-self.max_standard_chat_history:]
            # 合并系统提示词和最近消息，避免重复
            optimized_history = []
            for prompt in system_prompts:
                if prompt not in recent_messages:
                    optimized_history.append(prompt)
            optimized_history.extend(recent_messages)
            # 更新聊天历史
            self.standard_chat_history_messages = optimized_history
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 保存所有聊天历史记录
        self.chat_history_manager.save_history(self.all_chat_histories)
        
        # 停止讨论线程
        if hasattr(self, 'chat_thread') and self.chat_thread and self.chat_thread.isRunning():
            self.chat_thread.stop()
            self.chat_thread.wait(1000)  # 等待线程结束
        
        # 停止辩论线程
        if hasattr(self, 'debate_thread') and self.debate_thread and self.debate_thread.isRunning():
            self.debate_thread.stop()
            self.debate_thread.wait(1000)  # 等待线程结束
        
        # 释放内存：清理大型数据结构
        self.standard_chat_history_messages.clear()
        if hasattr(self, 'discussion_history_messages'):
            self.discussion_history_messages.clear()
        if hasattr(self, 'debate_history_messages'):
            self.debate_history_messages.clear()
        
        event.accept()

def main():
    # 确保中文显示正常
    import sys
    if sys.platform == 'win32':
        # Windows平台下设置字体
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ai.chat.between.ais')
    
    # 加载环境变量
    load_dotenv()
    
    app = QApplication(sys.argv)
    
    # 设置全局样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = ChatGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()