# -*- coding: utf-8 -*-
"""
辩论标签页组件，用于实现双AI辩论功能
"""

import os
import datetime
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from utils.logger_config import get_logger
from utils.config_manager import config_manager

# 导入子组件
from .config_panel import DebateConfigPanel
from .ai_config_panel import AIDebateConfigPanel
from .chat_history_panel import DebateChatHistoryPanel
from .controls_panel import DebateControlsPanel

# 导入线程和管理工具
from utils.thread_manager import DebateThread, SummaryThread
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class DebateTabWidget(QWidget):
    """
    辩论标签页组件，用于实现双AI辩论功能

    信号:
        update_signal: 更新聊天历史信号，参数为(发送者, 内容, 模型名称)
        update_status_signal: 更新状态信号，参数为状态信息
    """

    # 定义信号
    update_signal = pyqtSignal(str, str, str)
    update_status_signal = pyqtSignal(str)

    def __init__(self, api_settings_widget):
        """初始化辩论标签页组件

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()

        # 保存API设置组件引用
        self.api_settings_widget = api_settings_widget

        # 聊天历史内存优化设置
        self.max_debate_history = 50  # 设置辩论历史的最大消息数量

        # 聊天历史计数（用于内存优化）
        self.debate_chat_count = 0  # 跟踪当前辩论历史数量

        # 辩论历史存储（用于API调用）
        self.debate_history_messages = []

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
        self.config_panel = DebateConfigPanel()

        # AI配置面板
        self.ai_config_panel = AIDebateConfigPanel(self.api_settings_widget)

        # 聊天历史面板
        self.chat_history_panel = DebateChatHistoryPanel()

        # 控制面板
        self.controls_panel = DebateControlsPanel()

    def init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加配置面板
        layout.addWidget(self.config_panel)

        # 添加AI配置面板
        layout.addWidget(self.ai_config_panel)

        # 添加聊天历史面板，设置权重为1，占据剩余空间
        layout.addWidget(self.chat_history_panel, 1)

        # 添加控制面板
        layout.addWidget(self.controls_panel)

        self.setLayout(layout)

    def connect_signals(self):
        """连接各个组件的信号"""
        # 连接控制面板信号
        self.controls_panel.start_signal.connect(self.start_debate)
        self.controls_panel.stop_signal.connect(self.stop_debate)
        self.controls_panel.save_history_signal.connect(self.save_debate_history)
        self.controls_panel.load_history_signal.connect(self.load_debate_history)
        self.controls_panel.export_pdf_signal.connect(self.export_debate_history_to_pdf)

    def start_debate(self):
        """
        开始双AI辩论，处理用户点击"开始辩论"按钮的事件
        """
        # 获取并验证辩论主题
        topic = self.config_panel.get_topic()
        if not topic:
            QMessageBox.warning(
                self,
                i18n.translate("warning"),
                i18n.translate("please_enter_debate_topic"),
            )
            return

        # 更新UI状态，防止重复点击
        self.controls_panel.set_controls_enabled(False, True)

        # 更新状态信息
        self.update_status(i18n.translate("initializing_debate"))

        # 清空辩论历史，准备新的辩论
        self.chat_history_panel.clear_debate_history()

        # 显示辩论开始消息，告知用户辩论主题
        self.chat_history_panel.append_to_debate_history("系统", f"{i18n.translate('debate_topic')}: {topic}")

        # 获取用户配置的辩论参数
        api1, model1 = self.ai_config_panel.get_ai1_config()
        api2, model2 = self.ai_config_panel.get_ai2_config()
        rounds = self.config_panel.get_rounds()
        temperature = self.config_panel.get_temperature()
        time_limit = self.config_panel.get_time_limit()

        # 显示辩论配置，让用户了解当前辩论的设置
        api3, model3 = self.ai_config_panel.get_ai3_config()
        self.chat_history_panel.append_to_debate_history(
            "系统",
            f"{i18n.translate('debate_config')}: {i18n.translate('pro_ai1')}({api1}:{model1}) vs {i18n.translate('con_ai2')}({api2}:{model2})，<br>{i18n.translate('referee_ai3')}({api3}:{model3})，{i18n.translate('total_rounds')} {rounds}，{i18n.translate('temperature')} {temperature}",
        )

        # 创建DebateThread实例，传入所有必要参数
        self.chat_thread = DebateThread(
            topics=[topic],
            model1_name=model1,
            model2_name=model2,
            model1_api=api1,
            model2_api=api2,
            rounds=rounds,
            time_limit=time_limit,
            api_settings_widget=self.api_settings_widget,
            temperature=temperature,
        )

        # 连接线程信号到相应的处理方法
        self.chat_thread.update_signal.connect(
            self.chat_history_panel.append_to_debate_history
        )  # 接收辩论历史更新
        self.chat_thread.status_signal.connect(self.update_status)  # 接收状态更新
        self.chat_thread.finished_signal.connect(
            self._on_debate_finished
        )  # 接收辩论结束信号
        self.chat_thread.error_signal.connect(self._on_debate_error)  # 接收辩论错误信号
        self.chat_thread.stream_update_signal.connect(
            self.chat_history_panel.on_stream_update
        )  # 接收流式更新

        # 启动辩论线程，开始双AI辩论
        self.chat_thread.start()
        logger.info(f"辩论已启动，主题: {topic}")

    def stop_debate(self):
        """
        停止双AI辩论，处理用户点击"停止辩论"按钮的事件
        """
        # 检查辩论线程是否存在
        if self.chat_thread:
            # 断开辩论线程的信号连接
            try:
                self.chat_thread.update_signal.disconnect()
                self.chat_thread.status_signal.disconnect()
                self.chat_thread.finished_signal.disconnect()
                self.chat_thread.error_signal.disconnect()
                self.chat_thread.stream_update_signal.disconnect()
            except Exception as e:
                logger.debug(f"断开辩论线程信号连接时出错: {str(e)}")
            
            # 如果线程正在运行，停止它
            if self.chat_thread.isRunning():
                self.chat_thread.stop()
                self.update_status(i18n.translate("stopping_debate"))
            
            # 清理线程资源
            self.chat_thread = None

        # 检查总结线程是否存在
        if self.summary_thread:
            # 断开总结线程的信号连接
            try:
                self.summary_thread.update_signal.disconnect()
                self.summary_thread.status_signal.disconnect()
                self.summary_thread.finished_signal.disconnect()
                self.summary_thread.error_signal.disconnect()
                self.summary_thread.stream_update_signal.disconnect()
            except Exception as e:
                logger.debug(f"断开总结线程信号连接时出错: {str(e)}")
            
            # 如果线程正在运行，停止它
            if self.summary_thread.isRunning():
                self.summary_thread.stop()
            
            # 清理线程资源
            self.summary_thread = None

        # 恢复UI状态，允许用户重新开始辩论
        self.controls_panel.set_controls_enabled(True, False)
        logger.info("辩论已停止")

    def _on_debate_finished(self):
        """
        处理辩论结束信号，当辩论线程完成所有轮次辩论后调用
        """
        # 更新状态信息，告知用户辩论已完成并开始生成总结
        self.update_status(i18n.translate("debate_completed_generating_judgment"))
        # 更新UI状态
        self.controls_panel.set_controls_enabled(False, False)

        # 获取辩论历史记录，用于生成总结
        debate_history = self.chat_thread.get_debate_history()

        # 构建辩论历史文本，过滤掉系统提示词
        debate_text = ""
        for msg in debate_history:
            if msg["role"] == "system":
                continue  # 跳过系统提示词
            debate_text += f"{msg['role']}: {msg['content']}\n\n"

        # 获取AI3的配置信息
        api3, model3 = self.ai_config_panel.get_ai3_config()

        # 构建AI3的系统提示词
        topic = self.config_panel.get_topic()
        ai3_system_prompt = config_manager.get("debate.judge_ai3_prompt", "").format(topic=topic)

        # 构建完整的辩论文本，包含主题和历史
        full_debate_text = f"辩论主题: {topic}\n\n辩论历史:\n{debate_text}"

        # 构建AI3的消息，包含系统提示词和讨论历史
        ai3_messages = [
            {"role": "system", "content": ai3_system_prompt},
            {"role": "user", "content": full_debate_text},
        ]

        # 创建AI3总结线程
        self.summary_thread = SummaryThread(
            model_name=model3,
            model_api=api3,
            messages=ai3_messages,
            api_settings_widget=self.api_settings_widget,
            temperature=self.config_panel.get_temperature(),
        )

        # 连接总结线程信号到相应的处理方法
        self.summary_thread.update_signal.connect(
            self.chat_history_panel.append_to_debate_history
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

        # 启动总结线程，开始生成辩论总结
        self.summary_thread.start()
        logger.info("辩论已完成，开始生成裁判报告")

    def _on_summary_finished(self):
        """
        处理总结完成信号，当AI3完成总结后调用
        """

        self.update_signal.emit(
            "系统", f"=== {i18n.translate('debate_judgment_completed')} ===", ""
        )

        # 更新状态信息
        self.update_status(i18n.translate("judgment_report_generated"))
        # 恢复UI状态
        self.controls_panel.set_controls_enabled(True, False)
        # 清理总结线程资源
        self.summary_thread = None
        # 清理讨论线程资源（延迟清理，确保总结已生成）
        self.chat_thread = None
        
        # 自动保存辩论历史到历史管理器
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
                
                # 获取辩论主题
                topic = self.config_panel.get_topic()
                
                # 保存历史记录
                history_manager.add_history(
                    func_type="辩论",
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
                logger.info("辩论历史已自动保存到历史管理器")
            
            self.chat_history_panel.debate_history_text.page().toHtml(get_html_finished)
        except Exception as e:
            logger.error(f"自动保存辩论历史到历史管理器失败: {str(e)}")
        
        logger.info("裁判报告生成完成，所有线程资源已清理")

    def _on_summary_error(self, error):
        """
        处理总结错误信号，当AI3总结过程中发生错误时调用

        Args:
            error: 错误信息
        """
        # 记录错误日志
        logger.error(f"{i18n.translate('judgment_report_error')}: {error}")
        # 显示错误信息到讨论历史
        self.chat_history_panel.append_to_debate_history(
            "系统", f"{i18n.translate('judgment_report_error')}: {error}"
        )
        # 更新状态信息
        self.update_status(i18n.translate("judgment_report_failed"))
        # 恢复UI状态
        self.controls_panel.set_controls_enabled(True, False)
        # 清理总结线程资源
        self.summary_thread = None

    def _on_debate_error(self, error):
        """
        处理辩论错误信号，当辩论过程中发生错误时调用

        Args:
            error: 错误信息
        """
        # 记录错误日志
        logger.error(f"{i18n.translate('debate_error')}: {error}")
        # 显示错误信息到讨论历史
        self.chat_history_panel.append_to_debate_history("系统", f"{i18n.translate('debate_error')}: {error}")
        # 更新状态信息
        self.update_status(i18n.translate("debate_failed"))
        # 恢复UI状态
        self.controls_panel.set_controls_enabled(True, False)
        # 清理讨论线程资源
        self.chat_thread = None

    def update_status(self, status):
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self.controls_panel.update_status(status)
        self.update_status_signal.emit(status)

    def save_debate_history(self):
        """
        保存辩论历史到文件
        """
        try:
            # 生成默认文件名：Nonead-Debate-yyyyMMdd-HHmmss.json
            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Debate-{current_time.strftime('%Y%m%d-%H%M%S')}.json"
            )

            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.translate("save_debate_history"),
                default_filename,
                "JSON Files (*.json)",
            )

            if file_path:
                # 获取辩论主题
                topic = self.config_panel.get_topic()

                # 收集辩论历史数据
                debate_history = {
                    "type": "debate",
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
                    # 更新历史数据
                    debate_history["html_content"] = html

                    # 保存到JSON文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        import json

                        json.dump(debate_history, f, ensure_ascii=False, indent=2)

                    QMessageBox.information(
                        self,
                        i18n.translate("success"),
                        i18n.translate("debate_history_saved", path=file_path),
                    )

                self.chat_history_panel.debate_history_text.page().toHtml(
                    get_html_finished
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("debate_history_save_failed", error=str(e)),
            )

    def load_debate_history(self):
        """
        从文件加载辩论历史
        """
        try:
            # 打开文件对话框，让用户选择加载文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, i18n.translate("load_debate_history"), "", "JSON Files (*.json)"
            )

            if file_path:
                # 从JSON文件加载辩论历史
                with open(file_path, "r", encoding="utf-8") as f:
                    import json

                    debate_history = json.load(f)

                # 清空当前内容
                self.chat_history_panel.clear_debate_history()

                # 直接设置HTML内容
                if "html_content" in debate_history:
                    self.chat_history_panel.debate_history_text.setHtml(
                        debate_history["html_content"]
                    )

                # 更新辩论配置
                if "topic" in debate_history:
                    self.config_panel.debate_topic_edit.setText(debate_history["topic"])
                if "model1" in debate_history:
                    self.ai_config_panel.model1_combo.setCurrentText(
                        debate_history["model1"]
                    )
                if "api1" in debate_history:
                    index = self.ai_config_panel.api1_combo.findText(
                        debate_history["api1"]
                    )
                    if index != -1:
                        self.ai_config_panel.api1_combo.blockSignals(True)
                        self.ai_config_panel.api1_combo.setCurrentIndex(index)
                        self.ai_config_panel.api1_combo.blockSignals(False)
                if "model2" in debate_history:
                    self.ai_config_panel.model2_combo.setCurrentText(
                        debate_history["model2"]
                    )
                if "api2" in debate_history:
                    index = self.ai_config_panel.api2_combo.findText(
                        debate_history["api2"]
                    )
                    if index != -1:
                        self.ai_config_panel.api2_combo.blockSignals(True)
                        self.ai_config_panel.api2_combo.setCurrentIndex(index)
                        self.ai_config_panel.api2_combo.blockSignals(False)
                if "model3" in debate_history:
                    self.ai_config_panel.model3_combo.setCurrentText(
                        debate_history["model3"]
                    )
                if "api3" in debate_history:
                    index = self.ai_config_panel.api3_combo.findText(
                        debate_history["api3"]
                    )
                    if index != -1:
                        self.ai_config_panel.api3_combo.blockSignals(True)
                        self.ai_config_panel.api3_combo.setCurrentIndex(index)
                        self.ai_config_panel.api3_combo.blockSignals(False)
                if "rounds" in debate_history:
                    self.config_panel.debate_rounds_spin.setValue(
                        debate_history["rounds"]
                    )
                if "temperature" in debate_history:
                    self.config_panel.debate_temp_spin.setValue(
                        debate_history["temperature"]
                    )
                if "time_limit" in debate_history:
                    self.config_panel.debate_time_limit_spin.setValue(
                        debate_history["time_limit"]
                    )

                QMessageBox.information(
                    self,
                    i18n.translate("success"),
                    i18n.translate("debate_history_loaded", path=file_path),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("debate_history_load_failed", error=str(e)),
            )

    def export_debate_history_to_pdf(self):
        """
        将辩论历史导出为PDF文件
        """
        try:
            # 生成默认文件名：Nonead-Debate-yyyyMMdd-HHmmss.pdf
            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Debate-{current_time.strftime('%Y%m%d-%H%M%S')}.pdf"
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
                        self.chat_history_panel.debate_history_text.setHtml(new_html)

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
                                                "debate_history_exported",
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
                                            self.chat_history_panel.debate_history_text.setHtml(
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
                                self.chat_history_panel.debate_history_text.page().pdfPrintingFinished.disconnect(
                                    handle_pdf_printing_finished
                                )
                                pdf_exported(success)

                            # 连接信号
                            self.chat_history_panel.debate_history_text.page().pdfPrintingFinished.connect(
                                handle_pdf_printing_finished
                            )

                            # 调用PDF导出方法，仅传入文件路径
                            self.chat_history_panel.debate_history_text.page().printToPdf(
                                file_path
                            )

                        # 延迟1000毫秒确保HTML渲染完成
                        QTimer.singleShot(1000, export_pdf)

                self.chat_history_panel.debate_history_text.page().toHtml(
                    get_html_finished
                )
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
        self.stop_debate()
        
        # 调用所有子组件的reinit_ui方法
        self.config_panel.reinit_ui()
        self.ai_config_panel.reinit_ui()
        self.chat_history_panel.reinit_ui()
        self.controls_panel.reinit_ui()
