# -*- coding: utf-8 -*-
"""
批量处理标签页组件
"""

import sys
import os
import time
from utils.logger_config import get_logger
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 导入模型管理器
from utils.model_manager import model_manager
from utils.i18n_manager import i18n

# 导入子组件
from .batch.config_panel import BatchConfigPanel
from .batch.ai_config_panel import AIBatchConfigPanel
from .batch.results_panel import BatchResultsPanel
from .batch.controls_panel import BatchControlsPanel

# 获取日志记录器
logger = get_logger(__name__)


class BatchProcessingTabWidget(QWidget):
    """
    批量处理标签页组件，用于实现批量处理功能

    信号:
        update_status_signal: 更新状态信号，参数为状态信息
    """

    # 定义信号
    update_status_signal = pyqtSignal(str)

    def __init__(self, api_settings_widget):
        """
        初始化批量处理标签页组件

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()

        # 保存API设置组件引用
        self.api_settings_widget = api_settings_widget

        # 批量历史设置
        self.max_batch_history = 100  # 设置批量历史的最大消息数量
        self.batch_chat_count = 0  # 跟踪当前批量历史数量
        self.batch_history_messages = []  # 批量历史存储（用于API调用）
        self.batch_history_html = ""  # 批量历史HTML内容（用于历史记录）

        # 批量处理线程
        self.batch_thread = None
        self.is_processing = False
        self.is_paused = False

        # 初始化组件
        self.init_components()

        # 初始化UI
        self.init_ui()

        # 连接信号
        self.connect_signals()

        # 连接语言变化信号
        from utils.i18n_manager import i18n

        i18n.language_changed.connect(self.reinit_ui)

    def init_components(self):
        """
        初始化各个子组件
        """
        # 配置面板
        self.config_panel = BatchConfigPanel()

        # AI配置面板
        self.ai_config_panel = AIBatchConfigPanel(self.api_settings_widget)

        # 结果显示面板
        self.results_panel = BatchResultsPanel()
        # 初始化结果标题
        self.results_panel.update_result_title(self.config_panel.get_batch_type())

        # 控制面板
        self.controls_panel = BatchControlsPanel()

    def init_ui(self):
        """
        初始化UI布局
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 配置区域
        self.config_group = QGroupBox(i18n.translate("batch_processing_config"))
        self.config_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        config_layout.setContentsMargins(10, 5, 10, 10)

        # 添加配置面板
        config_layout.addWidget(self.config_panel)

        # 添加AI配置面板
        config_layout.addWidget(self.ai_config_panel)

        self.config_group.setLayout(config_layout)
        layout.addWidget(self.config_group)

        # 添加结果显示面板
        layout.addWidget(self.results_panel, 1)  # 设置权重为1，占据剩余空间

        # 添加控制面板
        layout.addWidget(self.controls_panel)

        self.setLayout(layout)

    def connect_signals(self):
        """
        连接信号
        """
        # 配置面板信号
        self.config_panel.batch_type_changed.connect(
            self.ai_config_panel.on_batch_type_changed
        )
        self.config_panel.batch_type_changed.connect(
            self.results_panel.update_result_title
        )

        # 控制面板信号
        self.controls_panel.load_tasks_button.clicked.connect(self.load_tasks)
        self.controls_panel.save_results_button.clicked.connect(self.save_results)
        self.controls_panel.save_history_button.clicked.connect(self.save_batch_history)
        self.controls_panel.load_history_button.clicked.connect(self.load_batch_history)
        self.controls_panel.start_batch_button.clicked.connect(
            self.start_batch_processing
        )
        self.controls_panel.stop_batch_button.clicked.connect(
            self.stop_batch_processing
        )

    def update_status(self, status):
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self.controls_panel.update_status(status)
        self.update_status_signal.emit(status)

    def load_tasks(self):
        """
        从文件加载批量任务，使用流式读取处理大文件
        """
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载任务文件", "", "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # 使用流式读取，避免一次性加载大文件到内存
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 清空现有任务并添加新任务
                self.config_panel.task_edit.clear()
                self.config_panel.task_edit.insertPlainText(content)

                # 手动触发任务数量更新
                self.config_panel.update_task_count()
                self.update_status("已从文件加载任务")
        except FileNotFoundError as e:
            error_msg = f"文件未找到: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        except PermissionError as e:
            error_msg = f"权限错误: 无法读取文件，错误信息: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            error_msg = f"加载任务失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def clear_results(self):
        """
        清空结果显示
        """
        self.results_panel.clear_results()

    def save_results(self):
        """
        保存处理结果到文件
        """
        try:
            # 从Web浏览器控件获取HTML内容
            def get_html_callback(html):
                """
                获取HTML内容后的回调函数
                """
                if not html:
                    QMessageBox.warning(self, "警告", "结果为空，无法保存")
                    return

                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存结果文件",
                    "",
                    "HTML Files (*.html);;Text Files (*.txt);;All Files (*)",
                )

                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    self.update_status(f"结果已保存到文件: {file_path}")

            # 异步获取HTML内容
            self.results_panel.result_text.page().toHtml(get_html_callback)
        except Exception as e:
            error_msg = f"保存结果失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def save_batch_history(self):
        """
        保存批量历史到文件
        """
        try:
            # 从Web浏览器控件获取HTML内容
            def get_html_callback(html):
                """
                获取HTML内容后的回调函数
                """
                if not html:
                    QMessageBox.warning(self, "警告", "批量历史为空，无法保存")
                    return

                file_path, _ = QFileDialog.getSaveFileName(
                    self, "保存批量历史", "", "HTML Files (*.html);;All Files (*)"
                )

                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    self.update_status(f"批量历史已保存到文件: {file_path}")

            # 异步获取HTML内容
            self.results_panel.result_text.page().toHtml(get_html_callback)
        except Exception as e:
            error_msg = f"保存批量历史失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def load_batch_history(self):
        """
        从文件加载批量处理历史
        """
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载批量历史", "", "HTML Files (*.html);;All Files (*)"
            )

            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # 显示加载的历史
                self.results_panel.result_text.setHtml(html_content)
                self.results_panel.batch_history_html = html_content
                self.update_status(f"批量历史已从 {file_path} 加载")
        except Exception as e:
            error_msg = f"加载批量历史失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def start_batch_processing(self):
        """
        开始批量处理
        """
        tasks = self.config_panel.get_tasks()
        if not tasks:
            QMessageBox.warning(self, "警告", "请输入或加载批量任务")
            return

        # 清空结果
        self.results_panel.clear_results()

        # 更新状态
        self.update_status("正在进行批量处理...")

        # 禁用开始按钮，启用停止按钮
        self.controls_panel.set_controls_enabled(False, True)
        self.is_processing = True

        # 创建批量处理线程
        from PyQt5.QtCore import QThread, pyqtSignal

        class BatchProcessingWorker(QThread):
            """
            批量处理工作线程
            """

            # 定义信号
            update_result = pyqtSignal(str, str)  # 结果更新信号
            update_status = pyqtSignal(str)  # 状态更新信号
            task_complete = pyqtSignal()  # 单个任务完成信号
            finished = pyqtSignal()  # 全部完成信号
            error = pyqtSignal(str)  # 错误信号

            def __init__(
                self,
                parent,
                tasks,
                batch_type,
                ai1_api,
                ai1_model,
                ai2_api,
                ai2_model,
                ai3_api,
                ai3_model,
                rounds,
                temperature,
            ):
                super().__init__(parent)
                self.parent = parent
                self.tasks = tasks
                self.batch_type = batch_type
                self.ai1_api = ai1_api
                self.ai1_model = ai1_model
                self.ai2_api = ai2_api
                self.ai2_model = ai2_model
                self.ai3_api = ai3_api
                self.ai3_model = ai3_model
                self.rounds = rounds
                self.temperature = temperature
                self.is_processing = True

            def run(self):
                """
                线程运行函数
                """
                try:
                    total_tasks = len(self.tasks)
                    completed_tasks = 0
                    failed_tasks = 0

                    # 显示批量处理标题
                    self.update_result.emit(f"批量{self.batch_type}处理开始", "system")
                    self.update_result.emit(f"开始处理 {total_tasks} 个任务", "info")

                    # 处理每个任务
                    for i, task in enumerate(self.tasks):
                        if not self.is_processing or not self.parent.is_processing:
                            break

                        try:
                            # 更新进度，使用浮点数除法确保计算正确
                            progress = int((float(i + 1) / total_tasks) * 100)
                            self.update_result.emit(
                                f"进度: {progress}% - 处理任务 {i+1}/{total_tasks}: {task}",
                                "info",
                            )
                            self.update_status.emit(f"批量处理中: {progress}%")

                            # 执行单个任务
                            result = self.parent._execute_single_task(task, i)

                            # 任务完成
                            self.update_result.emit(
                                f"任务 {i+1} 完成: {task}", "success"
                            )
                            self.update_result.emit(f"结果: {result}", "result")
                            self.update_result.emit("-" * 50, "system")
                            completed_tasks += 1

                        except Exception as e:
                            # 任务失败
                            error_msg = f"{str(e)}"
                            self.update_result.emit(f"任务 {i+1} 失败: {task}", "error")
                            self.update_result.emit(f"错误: {error_msg}", "error")
                            self.update_result.emit("-" * 50, "system")
                            failed_tasks += 1

                    # 发送完成消息
                    self.update_result.emit(f"进度: 100% - 批量处理完成", "info")

                    # 显示处理结果
                    import time

                    end_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.update_result.emit("=" * 60, "system")

                    summary = (
                        f"**批量{self.batch_type}处理完成**\n"
                        f"- 总任务数: {total_tasks}\n"
                        f"- 完成任务: {completed_tasks}\n"
                        f"- 失败任务: {failed_tasks}\n"
                        f"- 结束时间: {end_time}"
                    )

                    self.update_result.emit(summary, "success")
                    self.update_status.emit("批量处理完成")

                except Exception as e:
                    error_msg = f"批量处理失败: {str(e)}"
                    self.error.emit(error_msg)
                finally:
                    self.finished.emit()

            def stop(self):
                """
                停止线程
                """
                self.is_processing = False

        # 获取配置
        batch_type = self.config_panel.get_batch_type()
        ai1_api, ai1_model = self.ai_config_panel.get_ai1_config()
        ai2_api, ai2_model = self.ai_config_panel.get_ai2_config()
        ai3_api, ai3_model = self.ai_config_panel.get_ai3_config()
        rounds = self.config_panel.get_rounds()
        temperature = self.config_panel.get_temperature()

        # 创建并启动工作线程
        self.worker_thread = BatchProcessingWorker(
            self,
            tasks,
            batch_type,
            ai1_api,
            ai1_model,
            ai2_api,
            ai2_model,
            ai3_api,
            ai3_model,
            rounds,
            temperature,
        )

        # 连接信号
        self.worker_thread.update_result.connect(self.results_panel.append_to_result)
        self.worker_thread.update_status.connect(self.update_status)
        self.worker_thread.error.connect(
            lambda msg: self.results_panel.append_to_result(f"**错误**\n{msg}", "error")
        )

        def on_finished():
            """线程结束回调"""
            self.controls_panel.set_controls_enabled(True, False)
            self.is_processing = False
            self.worker_thread = None

        self.worker_thread.finished.connect(on_finished)

        # 启动线程
        self.worker_thread.start()

    def stop_batch_processing(self):
        """
        停止批量处理
        """
        self.is_processing = False
        if hasattr(self, "worker_thread") and self.worker_thread:
            self.worker_thread.stop()
        self.update_status("批量处理已停止")
        self.controls_panel.set_controls_enabled(True, False)

    def _execute_single_task(self, task, task_index):
        """
        执行单个批量任务

        Args:
            task: 任务内容
            task_index: 任务索引

        Returns:
            str: 任务执行结果
        """
        # 导入必要的线程类
        from utils.thread_manager import DiscussionThread, DebateThread
        from PyQt5.QtCore import QThread
        import time
        import threading

        # 根据批量类型执行不同的处理逻辑
        batch_type = self.config_panel.get_batch_type()
        result = f"任务 '{task}' 的处理结果\n"
        result += f"- 批量类型: {batch_type}\n"
        result += f"- 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # 存储线程执行结果
        task_result = []
        thread_finished = threading.Event()

        # 定义信号处理函数
        def handle_update(sender, content):
            """处理更新信号"""
            nonlocal task_result
            message = f"{sender}: {content}"
            task_result.append(message)
            self.results_panel.append_to_result(message, message_type="system")

        def handle_status(message):
            """处理状态信号"""
            self.update_status(message)

        def handle_error(message):
            """处理错误信号"""
            nonlocal task_result
            task_result.append(f"错误: {message}")
            self.results_panel.append_to_result(
                f"错误: {message}", message_type="error"
            )

        def handle_stream_update(sender, partial_content, model):
            """处理流式更新信号"""
            self.results_panel.append_to_result(
                f"{sender} ({model}): {partial_content}",
                message_type="result" if sender != "用户" else "info",
            )

        def handle_finished():
            """处理线程结束信号"""
            thread_finished.set()

        try:
            if batch_type == "讨论":
                # 创建讨论线程
                discussion_thread = DiscussionThread(
                    topic=task,
                    model1_name=self.ai_config_panel.batch_ai1_model_combo.currentText(),
                    model2_name=self.ai_config_panel.batch_ai2_model_combo.currentText(),
                    model3_name=self.ai_config_panel.batch_ai3_model_combo.currentText(),
                    model1_api=self.ai_config_panel.batch_ai1_api_combo.currentText(),
                    model2_api=self.ai_config_panel.batch_ai2_api_combo.currentText(),
                    model3_api=self.ai_config_panel.batch_ai3_api_combo.currentText(),
                    rounds=self.config_panel.get_rounds(),
                    time_limit=600,
                    api_settings_widget=self.api_settings_widget,
                    temperature=self.config_panel.get_temperature(),
                )

                # 连接信号
                discussion_thread.update_signal.connect(handle_update)
                discussion_thread.status_signal.connect(handle_status)
                discussion_thread.error_signal.connect(handle_error)
                discussion_thread.stream_update_signal.connect(handle_stream_update)
                discussion_thread.finished_signal.connect(handle_finished)

                # 启动线程
                discussion_thread.start()

                # 等待线程完成
                thread_finished.wait()

                # 获取讨论结果
                discussion_result = discussion_thread.get_discussion_history()
                for msg in discussion_result:
                    if msg["role"] != "system":
                        result += f"{msg['role']}: {msg['content']}\n\n"

            elif batch_type == "辩论":
                # 创建辩论线程
                debate_thread = DebateThread(
                    topic=task,
                    model1_name=self.ai_config_panel.batch_ai1_model_combo.currentText(),
                    model2_name=self.ai_config_panel.batch_ai2_model_combo.currentText(),
                    model3_name=self.ai_config_panel.batch_ai3_model_combo.currentText(),
                    model1_api=self.ai_config_panel.batch_ai1_api_combo.currentText(),
                    model2_api=self.ai_config_panel.batch_ai2_api_combo.currentText(),
                    model3_api=self.ai_config_panel.batch_ai3_api_combo.currentText(),
                    rounds=self.config_panel.get_rounds(),
                    time_limit=600,
                    api_settings_widget=self.api_settings_widget,
                    temperature=self.config_panel.get_temperature(),
                )

                # 连接信号
                debate_thread.update_signal.connect(handle_update)
                debate_thread.status_signal.connect(handle_status)
                debate_thread.error_signal.connect(handle_error)
                debate_thread.stream_update_signal.connect(handle_stream_update)
                debate_thread.finished_signal.connect(handle_finished)

                # 启动线程
                debate_thread.start()

                # 等待线程完成
                thread_finished.wait()

                # 获取辩论结果
                debate_result = debate_thread.get_debate_history()
                for msg in debate_result:
                    if msg["role"] != "system":
                        result += f"{msg['role']}: {msg['content']}\n\n"

            result += f"- 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            return result
        except Exception as e:
            logger.error(f"执行单个任务失败: {str(e)}")
            raise

    def reinit_ui(self):
        """
        更新UI文本，用于语言切换时更新界面
        """
        # 导入国际化管理器
        from utils.i18n_manager import i18n

        # 更新配置组标题
        if hasattr(self, 'config_group'):
            self.config_group.setTitle(i18n.translate("batch_processing_config"))

        # 调用子组件的reinit_ui方法
        self.config_panel.reinit_ui()
        self.ai_config_panel.reinit_ui()
        self.results_panel.reinit_ui()
        self.controls_panel.reinit_ui()
