# -*- coding: utf-8 -*-
"""
讨论标签页组件，用于实现双AI讨论功能
"""

import time
import datetime
import json
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 导入子组件
from .config_panel import ConfigPanel
from .ai_config_panel import AIConfigPanel
from .chat_history_panel import ChatHistoryPanel
from .controls_panel import ControlsPanel

# 导入线程和工具
from utils.thread_manager import DiscussionThread, SummaryThread
from utils.logger_config import get_logger
from utils.i18n_manager import i18n
from utils.config_manager import config_manager

logger = get_logger(__name__)


class DiscussionTabWidget(QWidget):
    """
    讨论标签页组件，用于实现双AI讨论功能

    信号:
        update_signal: 更新讨论历史信号，参数为(发送者, 内容, 模型名称)
        update_status_signal: 更新状态信号，参数为状态信息
    """

    # 定义信号
    update_signal = pyqtSignal(str, str, str)
    update_status_signal = pyqtSignal(str)

    def __init__(self, api_settings_widget):
        """初始化讨论标签页组件

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()

        # 保存API设置组件引用
        self.api_settings_widget = api_settings_widget

        # 聊天历史内存优化设置
        self.max_discussion_history = 50  # 设置讨论历史的最大消息数量
        self.discussion_chat_count = 0  # 跟踪当前讨论历史数量

        # 初始化聊天线程
        self.chat_thread = None
        self.summary_thread = None

        # 流式输出相关变量
        self.current_stream_sender = None
        self.current_stream_model = None

        # 初始化UI组件
        self.init_components()

        # 初始化UI布局
        self.init_ui()

        # 连接信号
        self.connect_signals()

        # 连接语言变化信号
        from utils.i18n_manager import i18n

        i18n.language_changed.connect(self.reinit_ui)

    def init_components(self):
        """初始化各个子组件"""
        # 配置面板
        self.config_panel = ConfigPanel()

        # AI配置面板
        self.ai_config_panel = AIConfigPanel(self.api_settings_widget)

        # 聊天历史面板
        self.chat_history_panel = ChatHistoryPanel()

        # 控制面板
        self.controls_panel = ControlsPanel()

    def init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加配置面板
        layout.addWidget(self.config_panel)

        # 添加AI配置面板
        layout.addWidget(self.ai_config_panel)

        # 添加聊天历史面板
        layout.addWidget(self.chat_history_panel, 1)  # 设置权重为1，占据剩余空间

        # 添加控制面板
        layout.addWidget(self.controls_panel)

        self.setLayout(layout)

    def connect_signals(self):
        """连接各个组件的信号"""
        # 连接控制面板信号
        self.controls_panel.start_signal.connect(self.start_chat)
        self.controls_panel.stop_signal.connect(self.stop_chat)
        self.controls_panel.save_history_signal.connect(self.save_discussion_history)
        self.controls_panel.load_history_signal.connect(self.load_discussion_history)
        self.controls_panel.export_pdf_signal.connect(self.export_history_to_pdf)

    def start_chat(self):
        """
        开始双AI讨论，处理用户点击"开始讨论"按钮的事件
        """
        # 获取并验证讨论主题
        topic = self.config_panel.get_topic()
        if not topic:
            QMessageBox.warning(
                self,
                i18n.translate("warning"),
                i18n.translate("please_enter_discussion_topic"),
            )
            return

        try:
            # 确保之前的线程已停止
            self.stop_chat()

            # 更新UI状态，防止重复点击
            self.controls_panel.set_controls_enabled(False, True)

            # 更新状态信息
            self.update_status(i18n.translate("initializing_discussion"))

            # 清空讨论历史，准备新的讨论
            self.chat_history_panel.clear_discussion_history()

            # 显示讨论开始消息，告知用户讨论主题
            self.chat_history_panel.append_to_discussion_history(
                "系统", f"{i18n.translate('discussion_topic')}: {topic}"
            )

            # 获取用户配置的讨论参数
            api1, model1 = self.ai_config_panel.get_ai1_config()
            api2, model2 = self.ai_config_panel.get_ai2_config()
            rounds = self.config_panel.get_rounds()
            temperature = self.config_panel.get_temperature()
            time_limit = self.config_panel.get_time_limit()

            # 显示讨论配置，让用户了解当前讨论的设置
            api3, model3 = self.ai_config_panel.get_ai3_config()
            self.chat_history_panel.append_to_discussion_history(
                "系统",
                f"{i18n.translate('discussion_config')}: {i18n.translate('scholar_ai1')}({api1}:{model1}) vs {i18n.translate('scholar_ai2')}({api2}:{model2})，<br>{i18n.translate('expert_ai3')}({api3}:{model3})，{i18n.translate('total_rounds')} {rounds}，{i18n.translate('temperature')} {temperature}",
            )

            # 创建DiscussionThread实例，传入所有必要参数
            self.chat_thread = DiscussionThread(
                topic=topic,
                model1_name=model1,
                model2_name=model2,
                model1_api=api1,
                model2_api=api2,
                rounds=rounds,
                time_limit=time_limit,
                api_settings_widget=self.api_settings_widget,
                temperature=temperature,
                config_panel=self.config_panel,
            )

            # 连接线程信号到相应的处理方法
            self.chat_thread.update_signal.connect(
                self.chat_history_panel.append_to_discussion_history
            )  # 接收讨论历史更新
            self.chat_thread.status_signal.connect(self.update_status)  # 接收状态更新
            self.chat_thread.finished_signal.connect(
                self._on_discussion_finished
            )  # 接收讨论结束信号
            self.chat_thread.error_signal.connect(
                self._on_discussion_error
            )  # 接收讨论错误信号
            self.chat_thread.stream_update_signal.connect(
                self.chat_history_panel.on_stream_update
            )  # 接收流式更新

            # 启动讨论线程，开始双AI讨论
            self.chat_thread.start()
            logger.info(f"讨论已启动，主题: {topic}")
        except Exception as e:
            logger.error(f"启动讨论失败: {str(e)}")
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("discussion_start_failed", error=str(e)),
            )
            self.controls_panel.set_controls_enabled(True, False)
            self.update_status(i18n.translate("discussion_start_failed"))

    def stop_chat(self):
        """
        停止双AI讨论，处理用户点击"停止讨论"按钮的事件
        """
        try:
            # 检查讨论线程是否存在且正在运行
            if self.chat_thread:
                if self.chat_thread.isRunning():
                    # 调用线程的stop方法停止讨论
                    self.chat_thread.stop()
                    # 更新状态信息，告知用户正在停止讨论
                    self.update_status(i18n.translate("stopping_discussion"))
                # 断开信号连接，避免内存泄漏
                self.chat_thread.update_signal.disconnect()
                self.chat_thread.status_signal.disconnect()
                self.chat_thread.finished_signal.disconnect()
                self.chat_thread.error_signal.disconnect()
                self.chat_thread.stream_update_signal.disconnect()
                # 清理线程资源
                self.chat_thread = None

            # 检查总结线程是否存在且正在运行
            if self.summary_thread:
                if self.summary_thread.isRunning():
                    # 调用线程的stop方法停止总结
                    self.summary_thread.stop()
                # 断开信号连接，避免内存泄漏
                self.summary_thread.update_signal.disconnect()
                self.summary_thread.status_signal.disconnect()
                self.summary_thread.finished_signal.disconnect()
                self.summary_thread.error_signal.disconnect()
                self.summary_thread.stream_update_signal.disconnect()
                # 清理线程资源
                self.summary_thread = None

            # 恢复UI状态，允许用户重新开始讨论
            self.controls_panel.set_controls_enabled(True, False)
            self.update_status(i18n.translate("discussion_stopped"))
            logger.info(i18n.translate("discussion_stopped"))
        except Exception as e:
            logger.error(f"停止讨论失败: {str(e)}")

    def _on_discussion_finished(self):
        """
        处理讨论结束信号，当讨论线程完成所有轮次讨论后调用
        """
        try:
            # 更新状态信息，告知用户讨论已完成并开始生成总结
            self.update_status(i18n.translate("discussion_completed_generating_summary"))
            # 更新UI状态
            self.controls_panel.set_controls_enabled(False, False)

            # 获取讨论历史记录，用于生成总结
            discussion_history = []
            if self.chat_thread:
                discussion_history = self.chat_thread.get_discussion_history()
                # 断开讨论线程信号连接
                self.chat_thread.update_signal.disconnect()
                self.chat_thread.status_signal.disconnect()
                self.chat_thread.finished_signal.disconnect()
                self.chat_thread.error_signal.disconnect()
                self.chat_thread.stream_update_signal.disconnect()

            # 构建讨论历史文本，过滤掉系统提示词
            discussion_text = ""
            for msg in discussion_history:
                if msg["role"] == "system":
                    continue  # 跳过系统提示词
                discussion_text += f"{msg['role']}: {msg['content']}\n\n"

            # 获取AI3的配置信息
            api3, model3 = self.ai_config_panel.get_ai3_config()

            # 构建专家AI3的系统提示词
            topic = self.config_panel.get_topic()
            ai3_system_prompt = config_manager.get("discussion.expert_ai3_prompt", "").format(
                topic=topic
            )

            # 构建AI3的消息，包含系统提示词和讨论历史
            ai3_messages = [
                {"role": "system", "content": ai3_system_prompt},
                {"role": "user", "content": discussion_text},
            ]

            # 创建AI3总结线程
            self.summary_thread = SummaryThread(
                model_name=model3,
                model_api=api3,
                messages=ai3_messages,
                api_settings_widget=self.api_settings_widget,
                temperature=self.config_panel.get_temperature(),
                config_panel=self.config_panel,
            )

            # 连接总结线程信号到相应的处理方法
            self.summary_thread.update_signal.connect(
                self.chat_history_panel.append_to_discussion_history
            )  # 接收总结更新
            self.summary_thread.status_signal.connect(self.update_status)  # 接收总结状态
            self.summary_thread.finished_signal.connect(
                self._on_summary_finished
            )  # 接收总结完成信号
            self.summary_thread.error_signal.connect(
                self._on_summary_error
            )  # 接收总结错误信号
            self.summary_thread.stream_update_signal.connect(
                self.chat_history_panel.on_stream_update
            )  # 接收总结流式更新

            # 清理讨论线程资源
            if hasattr(self, "chat_thread") and self.chat_thread:
                self.chat_thread = None

            # 启动总结线程，开始生成讨论总结
            self.summary_thread.start()
            logger.info(i18n.translate("discussion_completed_starting_summary"))
        except Exception as e:
            logger.error(f"{i18n.translate('failed_to_process_discussion_end')}: {str(e)}")
            # 清理资源
            self.stop_chat()
            self.update_status(i18n.translate("failed_to_process_discussion_end"))

    def _on_summary_finished(self):
        """
        处理总结完成信号，当AI3完成总结后调用
        """
        try:
            # 更新状态信息
            self.update_status(i18n.translate("summary_completed"))
            # 恢复UI状态
            self.controls_panel.set_controls_enabled(True, False)
            
            # 断开总结线程信号连接
            if self.summary_thread:
                self.summary_thread.update_signal.disconnect()
                self.summary_thread.status_signal.disconnect()
                self.summary_thread.finished_signal.disconnect()
                self.summary_thread.error_signal.disconnect()
                self.summary_thread.stream_update_signal.disconnect()
            
            # 清理总结线程资源
            self.summary_thread = None
            
            # 清理讨论线程资源（如果还存在）
            if hasattr(self, "chat_thread") and self.chat_thread:
                try:
                    self.chat_thread.update_signal.disconnect()
                    self.chat_thread.status_signal.disconnect()
                    self.chat_thread.finished_signal.disconnect()
                    self.chat_thread.error_signal.disconnect()
                    self.chat_thread.stream_update_signal.disconnect()
                except:
                    pass
                self.chat_thread = None
            
            # 自动保存讨论历史到历史管理器
            try:
                from utils.chat_history_manager import ChatHistoryManager
                history_manager = ChatHistoryManager()
                
                # 获取当前时间
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 获取当前HTML内容
                def get_html_finished(html):
                    # 获取AI配置
                    api1, model1 = self.ai_config_panel.get_ai1_config()
                    api2, model2 = self.ai_config_panel.get_ai2_config()
                    api3, model3 = self.ai_config_panel.get_ai3_config()
                    
                    # 获取讨论主题
                    topic = self.config_panel.get_topic()
                    
                    # 保存历史记录
                    history_manager.add_history(
                        func_type="讨论",
                        topic=topic,
                        model1_name=model1,
                        model2_name=model2,
                        api1=api1,
                        api2=api2,
                        rounds=self.config_panel.get_rounds(),
                        chat_content=html,
                        start_time=current_time,
                        end_time=current_time,
                    )
                    logger.info(i18n.translate("discussion_history_auto_saved"))
                
                self.chat_history_panel.get_html_content(get_html_finished)
            except Exception as e:
                logger.error(f"{i18n.translate('failed_to_auto_save_discussion_history')}: {str(e)}")
            
            logger.info(i18n.translate("summary_completed_all_resources_cleaned"))
        except Exception as e:
            logger.error(f"{i18n.translate('failed_to_process_summary_completion')}: {str(e)}")
            # 确保UI状态恢复
            self.controls_panel.set_controls_enabled(True, False)
            self.update_status(i18n.translate("failed_to_process_summary_completion"))
            
    def _on_summary_error(self, error):
        """
        处理总结错误信号，当AI3总结过程中发生错误时调用

        Args:
            error: 错误信息
        """
        try:
            # 记录错误日志
            logger.error(f"{i18n.translate('summary_error')}: {error}")
            # 显示错误信息到讨论历史
            self.chat_history_panel.append_to_discussion_history(
                "系统", f"{i18n.translate('summary_error')}: {error}"
            )
            # 更新状态信息
            self.update_status(i18n.translate("summary_failed"))
            
            # 断开总结线程信号连接
            if self.summary_thread:
                try:
                    self.summary_thread.update_signal.disconnect()
                    self.summary_thread.status_signal.disconnect()
                    self.summary_thread.finished_signal.disconnect()
                    self.summary_thread.error_signal.disconnect()
                    self.summary_thread.stream_update_signal.disconnect()
                except:
                    pass
            
            # 恢复UI状态
            self.controls_panel.set_controls_enabled(True, False)
            # 清理总结线程资源
            self.summary_thread = None
            
            # 清理讨论线程资源（如果还存在）
            if hasattr(self, "chat_thread") and self.chat_thread:
                try:
                    self.chat_thread.update_signal.disconnect()
                    self.chat_thread.status_signal.disconnect()
                    self.chat_thread.finished_signal.disconnect()
                    self.chat_thread.error_signal.disconnect()
                    self.chat_thread.stream_update_signal.disconnect()
                except:
                    pass
                self.chat_thread = None
        except Exception as e:
            logger.error(f"{i18n.translate('failed_to_process_summary_error')}: {str(e)}")
            # 确保UI状态恢复
            self.controls_panel.set_controls_enabled(True, False)
            self.update_status(i18n.translate('failed_to_process_summary_error'))

    def _on_discussion_error(self, error):
        """
        处理讨论错误信号，当讨论过程中发生错误时调用

        Args:
            error: 错误信息
        """
        try:
            # 记录错误日志
            logger.error(f"{i18n.translate('discussion_error')}: {error}")
            # 显示错误信息到讨论历史
            self.chat_history_panel.append_to_discussion_history(
                "系统", f"{i18n.translate('discussion_error')}: {error}"
            )
            # 更新状态信息
            self.update_status(i18n.translate("discussion_failed"))
            
            # 断开讨论线程信号连接
            if self.chat_thread:
                try:
                    self.chat_thread.update_signal.disconnect()
                    self.chat_thread.status_signal.disconnect()
                    self.chat_thread.finished_signal.disconnect()
                    self.chat_thread.error_signal.disconnect()
                    self.chat_thread.stream_update_signal.disconnect()
                except:
                    pass
            
            # 恢复UI状态
            self.controls_panel.set_controls_enabled(True, False)
            # 清理讨论线程资源
            self.chat_thread = None
        except Exception as e:
            logger.error(f"{i18n.translate('failed_to_process_discussion_error')}: {str(e)}")
            # 确保UI状态恢复
            self.controls_panel.set_controls_enabled(True, False)
            self.update_status(i18n.translate('failed_to_process_discussion_error'))

    def update_status(self, status):
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self.controls_panel.update_status(status)
        self.update_status_signal.emit(status)

    def _optimize_discussion_history(self):
        """
        优化讨论历史, 限制历史记录数量
        """
        if self.discussion_chat_count >= self.max_discussion_history:
            # 优化讨论历史，保留最近的消息
            # 这里可以添加具体的优化逻辑
            pass

    def save_discussion_history(self):
        """
        保存讨论历史到文件
        """
        try:
            # 生成默认文件名：Nonead-Discussion-yyyyMMdd-HHmmss.json
            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Discussion-{current_time.strftime('%Y%m%d-%H%M%S')}.json"
            )

            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.translate("save_discussion_history"),
                default_filename,
                "JSON Files (*.json)",
            )

            if file_path:
                # 获取讨论主题
                topic = self.config_panel.get_topic()

                # 收集讨论历史数据
                discussion_history = {
                    "type": "discussion",
                    "topic": topic,
                    "model1": self.ai_config_panel.model1_combo.currentText(),
                    "api1": self.ai_config_panel.api1_combo.currentText(),
                    "model2": self.ai_config_panel.model2_combo.currentText(),
                    "api2": self.ai_config_panel.api2_combo.currentText(),
                    "model3": self.ai_config_panel.model3_combo.currentText(),
                    "api3": self.ai_config_panel.api3_combo.currentText(),
                    "rounds": self.config_panel.get_rounds(),
                    "temperature": self.config_panel.get_temperature(),
                    "time_limit": self.config_panel.get_time_limit(),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "html_content": "",
                }

                # 获取当前HTML内容
                def get_html_finished(html):
                    nonlocal discussion_history
                    discussion_history["html_content"] = html

                    # 保存到JSON文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(discussion_history, f, ensure_ascii=False, indent=2)

                    QMessageBox.information(
                        self,
                        i18n.translate("success"),
                        i18n.translate("discussion_history_saved", path=file_path),
                    )

                self.chat_history_panel.get_html_content(get_html_finished)
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("discussion_history_save_failed", error=str(e)),
            )

    def load_discussion_history(self):
        """
        从文件加载讨论历史
        """
        try:
            # 打开文件对话框，让用户选择加载文件
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                i18n.translate("load_discussion_history"),
                "",
                "JSON Files (*.json)",
            )

            if file_path:
                # 从JSON文件加载讨论历史
                with open(file_path, "r", encoding="utf-8") as f:
                    discussion_history = json.load(f)

                # 使用JavaScript清空当前内容
                js = """
                document.getElementById('discussion-body').innerHTML = '';
                window.scrollTo(0, 0);
                """

                # 直接设置HTML内容
                if "html_content" in discussion_history:
                    # 获取当前HTML结构
                    def get_current_html(html):
                        # 保留head部分，替换body内容
                        if "<body" in html and "</body>" in html:
                            body_start = html.find("<body")
                            body_end = html.find(">", body_start) + 1
                            body_close = html.rfind("</body>")

                            # 构建新的HTML
                            new_html = (
                                html[:body_end]
                                + discussion_history["html_content"]
                                + html[body_close:]
                            )
                            self.chat_history_panel.chat_history_text.setHtml(new_html)
                        else:
                            # 如果没有找到body标签，直接设置
                            self.chat_history_panel.chat_history_text.setHtml(
                                discussion_history["html_content"]
                            )

                    self.chat_history_panel.chat_history_text.page().toHtml(
                        get_current_html
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("discussion_history_load_failed", error=str(e)),
            )

    def export_history_to_pdf(self):
        """
        导出讨论历史到PDF文件
        """
        self.export_discussion_history_to_pdf()

    def export_discussion_history_to_pdf(self):
        """
        将讨论历史导出为PDF文件
        """
        try:
            # 生成默认文件名：Nonead-Discussion-yyyyMMdd-HHmmss.pdf
            import datetime

            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Discussion-{current_time.strftime('%Y%m%d-%H%M%S')}.pdf"
            )

            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.translate("export_pdf"),
                default_filename,
                "PDF Files (*.pdf)",
            )

            if file_path:
                # 保存原始HTML内容
                original_html = None

                # 获取当前HTML内容
                def get_html_finished(html):
                    nonlocal original_html
                    original_html = html

                    # 在body标签后添加头部信息
                    body_start_idx = html.find("<body")
                    if body_start_idx != -1:
                        # 找到body标签的结束位置
                        body_end_idx = html.find(">", body_start_idx) + 1

                        # 获取当前目录
                        import os
                        import sys

                        if getattr(sys, "frozen", False):
                            # 打包后的可执行文件所在目录
                            current_dir = os.path.dirname(sys.executable)
                        else:
                            # 开发环境下的当前文件所在目录
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            current_dir = os.path.dirname(current_dir)  # 向上一级目录
                            current_dir = os.path.dirname(current_dir)  # 再向上一级目录
                            current_dir = os.path.dirname(current_dir)  # 再向上一级目录

                        # 使用本地logo图片，转换为Base64编码嵌入HTML
                        import base64

                        # 使用资源管理器获取logo路径
                        from utils.resource_manager import ResourceManager
                        logo_path = ResourceManager.get_resource_path("noneadLogo.png")

                        # 将图片转换为Base64编码
                        try:
                            with open(logo_path, "rb") as f:
                                logo_data = f.read()
                            logo_base64 = base64.b64encode(logo_data).decode("utf-8")
                            # 构建Data URL
                            logo_url = f"data:image/png;base64,{logo_base64}"
                        except Exception as e:
                            # 如果读取失败，使用空的logo
                            logo_url = ""

                        # 创建头部HTML
                        header_html = f"""
                        <div style="text-align: center; margin-bottom: 20px; padding: 15px; border-bottom: 2px solid #ddd;">
                            <img src="{logo_url}" alt="NONEAD Logo" style="height: 60px; margin-bottom: 10px;">
                        </div>
                        """

                        # 构建新的HTML
                        new_html = (
                            html[:body_end_idx] + header_html + html[body_end_idx:]
                        )

                        # 直接设置web view的HTML内容
                        self.chat_history_panel.chat_history_text.setHtml(new_html)

                        # 使用QTimer延迟导出，确保HTML渲染完成
                        from PyQt5.QtCore import QTimer
                        from PyQt5.QtWidgets import QProgressDialog

                        def export_pdf():
                            # 创建进度对话框
                            progress_dialog = QProgressDialog(
                                "正在生成PDF文件...", "取消", 0, 100, self
                            )
                            progress_dialog.setWindowModality(Qt.WindowModal)
                            progress_dialog.setMinimumDuration(500)  # 500ms后显示进度条
                            progress_dialog.setValue(0)
                            progress_dialog.show()

                            # 定义PDF生成完成后的回调函数
                            def pdf_exported(success):
                                # 确保进度条达到100%
                                progress_dialog.setValue(100)  # 设置进度为100%

                                # 使用QTimer延迟关闭进度条，确保用户看到100%的状态
                                from PyQt5.QtCore import QTimer

                                def close_and_show_result():
                                    # 关闭进度条
                                    progress_dialog.close()

                                    if success:
                                        # 进度窗口关闭后，才显示成功对话框
                                        QMessageBox.information(
                                            self,
                                            i18n.translate("success"),
                                            i18n.translate(
                                                "discussion_history_exported",
                                                path=file_path,
                                            ),
                                        )
                                    else:
                                        QMessageBox.critical(
                                            self,
                                            i18n.translate("error"),
                                            i18n.translate("pdf_export_failed"),
                                        )

                                        # 恢复原始HTML内容
                                        if original_html:
                                            self.chat_history_panel.chat_history_text.setHtml(
                                                original_html
                                            )

                                # 延迟500ms后关闭进度条并显示结果
                                QTimer.singleShot(500, close_and_show_result)

                            # 更新进度条
                            def update_progress(value):
                                progress_dialog.setValue(value)

                            # 设置初始进度为50%，表示正在生成PDF
                            update_progress(50)

                            # 在PyQt5中，printToPdf方法不支持直接传递回调，而是通过信号通知
                            def handle_pdf_printing_finished(success):
                                # 断开信号连接，避免多次调用
                                self.chat_history_panel.chat_history_text.page().pdfPrintingFinished.disconnect(
                                    handle_pdf_printing_finished
                                )
                                pdf_exported(success)

                            # 连接信号
                            self.chat_history_panel.chat_history_text.page().pdfPrintingFinished.connect(
                                handle_pdf_printing_finished
                            )

                            # 调用PDF导出方法，仅传入文件路径
                            self.chat_history_panel.chat_history_text.page().printToPdf(
                                file_path
                            )

                        # 延迟1000毫秒确保HTML渲染完成
                        QTimer.singleShot(1000, export_pdf)

                self.chat_history_panel.get_html_content(get_html_finished)
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("pdf_export_failed", error=str(e)),
            )
            logger.error(f"导出PDF失败: {str(e)}")

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 在语言切换前停止所有正在运行的线程，避免UI更新冲突
        self.stop_chat()
        
        # 调用所有子组件的reinit_ui方法
        self.config_panel.reinit_ui()
        self.ai_config_panel.reinit_ui()
        self.chat_history_panel.reinit_ui()
        self.controls_panel.reinit_ui()
