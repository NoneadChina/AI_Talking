# -*- coding: utf-8 -*-
"""
聊天历史管理模块
负责聊天历史的保存、加载和导出功能
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class ChatHistoryManager:
    """
    聊天历史管理类，负责聊天历史的保存、加载和导出功能
    """
    
    def __init__(self, history_file='chat_histories.json'):
        """
        初始化聊天历史管理器
        
        Args:
            history_file (str, optional): 聊天历史文件路径. Defaults to 'chat_histories.json'.
        """
        self.history_file = history_file
        self.chat_histories = []
        self.max_history_size = 1000  # 限制最大历史记录数量，防止内存占用过高
    
    def load_history(self) -> List[Dict[str, Any]]:
        """
        从文件加载聊天历史
        
        Returns:
            list: 聊天历史列表
        """
        logger.info(f"正在从 {self.history_file} 加载聊天历史...")
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.chat_histories = json.load(f)
                logger.info(f"已从 {self.history_file} 加载 {len(self.chat_histories)} 条历史记录")
            else:
                self.chat_histories = []
                logger.info(f"{self.history_file} 不存在，创建空历史记录列表")
            return self.chat_histories
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {str(e)}")
            return []
        except PermissionError as e:
            logger.error(f"权限错误: 无法读取文件 {self.history_file}，错误信息: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: 文件 {self.history_file} 格式无效，错误信息: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"加载聊天历史失败: {str(e)}")
            return []
    
    def _prune_old_history(self):
        """
        修剪旧历史记录，保持在最大限制内
        """
        if len(self.chat_histories) > self.max_history_size:
            # 只保留最新的 max_history_size 条记录
            old_count = len(self.chat_histories) - self.max_history_size
            self.chat_histories = self.chat_histories[-self.max_history_size:]
            logger.info(f"已修剪 {old_count} 条旧历史记录，当前保留 {len(self.chat_histories)} 条")
    
    def save_history(self, history=None) -> bool:
        """
        保存聊天历史到文件
        
        Args:
            history (list, optional): 要保存的聊天历史列表. Defaults to None, 表示保存当前管理的历史.
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            if history is not None:
                self.chat_histories = history
            
            # 修剪旧历史记录
            self._prune_old_history()
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_histories, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存 {len(self.chat_histories)} 条历史记录到 {self.history_file}")
            return True
        except PermissionError as e:
            logger.error(f"权限错误: 无法写入文件 {self.history_file}，错误信息: {str(e)}")
            return False
        except IOError as e:
            logger.error(f"I/O错误: 写入文件 {self.history_file} 失败，错误信息: {str(e)}")
            return False
        except TypeError as e:
            logger.error(f"类型错误: 聊天历史数据包含不可序列化的类型，错误信息: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"JSON编码错误: 无法将聊天历史转换为JSON格式，错误信息: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"保存聊天历史失败: {str(e)}")
            return False
    
    def add_history(self, topic, model1_name, model2_name, api1, api2, rounds, chat_content, start_time, end_time):
        """
        添加聊天历史记录
        和同一个模型聊天，只记录一条历史，除非更换了模型
        
        Args:
            topic (str): 讨论主题
            model1_name (str): 模型1名称
            model2_name (str): 模型2名称
            api1 (str): 模型1 API类型
            api2 (str): 模型2 API类型
            rounds (int): 对话轮数
            chat_content (str): 聊天内容
            start_time (str): 开始时间
            end_time (str): 结束时间
        """
        # 检查是否存在相同模型组合的历史记录
        for i, existing_history in enumerate(self.chat_histories):
            # 对于单聊模式，只比较model1和api1
            if model2_name is None or model2_name == "":
                if existing_history["model1"] == model1_name and existing_history["api1"] == api1:
                    # 更新现有记录
                    self.chat_histories[i] = {
                        "topic": topic,
                        "model1": model1_name,
                        "model2": model2_name,
                        "api1": api1,
                        "api2": api2,
                        "rounds": rounds,
                        "chat_content": chat_content,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    return self.save_history()
            else:
                # 对于讨论/辩论模式，比较两个模型的组合
                if ((existing_history["model1"] == model1_name and existing_history["api1"] == api1 and
                     existing_history["model2"] == model2_name and existing_history["api2"] == api2) or
                    (existing_history["model1"] == model2_name and existing_history["api1"] == api2 and
                     existing_history["model2"] == model1_name and existing_history["api2"] == api1)):
                    # 更新现有记录
                    self.chat_histories[i] = {
                        "topic": topic,
                        "model1": model1_name,
                        "model2": model2_name,
                        "api1": api1,
                        "api2": api2,
                        "rounds": rounds,
                        "chat_content": chat_content,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    return self.save_history()
        
        # 如果没有相同模型组合的记录，添加新记录
        history = {
            "topic": topic,
            "model1": model1_name,
            "model2": model2_name,
            "api1": api1,
            "api2": api2,
            "rounds": rounds,
            "chat_content": chat_content,
            "start_time": start_time,
            "end_time": end_time
        }
        
        self.chat_histories.append(history)
        return self.save_history()
    
    def get_history_by_topic(self, topic):
        """
        根据主题获取聊天历史
        
        Args:
            topic (str): 讨论主题
            
        Returns:
            dict or None: 匹配的聊天历史记录，不存在返回None
        """
        for history in self.chat_histories:
            if history["topic"] == topic:
                return history
        return None
    
    def clear_history(self) -> bool:
        """
        清空聊天历史
        
        Returns:
            bool: 清空成功返回True，失败返回False
        """
        self.chat_histories = []
        return self.save_history()
    
    def delete_history(self, index) -> bool:
        """
        删除指定索引的聊天历史
        
        Args:
            index (int): 历史记录索引
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        if 0 <= index < len(self.chat_histories):
            del self.chat_histories[index]
            return self.save_history()
        return False
    
    def export_history_to_json(self, export_path) -> bool:
        """
        将聊天历史导出为JSON文件
        
        Args:
            export_path (str): 导出文件路径
            
        Returns:
            bool: 导出成功返回True，失败返回False
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.chat_histories, f, ensure_ascii=False, indent=2)
            logger.info(f"已将聊天历史导出到 {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出聊天历史到JSON失败: {str(e)}")
            return False
