# -*- coding: utf-8 -*-
"""
批量处理控制面板组件，负责批量处理的控制按钮和状态显示
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QFileDialog,
)
from utils.i18n_manager import i18n


class BatchControlsPanel(QWidget):
    """
    批量处理控制面板组件

    信号:
        load_tasks: 加载任务信号
        save_results: 保存结果信号
        save_history: 保存历史信号
        load_history: 加载历史信号
        start_batch: 开始批量处理信号
        stop_batch: 停止批量处理信号
    """

    # 定义信号
    load_tasks = pyqtSignal()
    save_results = pyqtSignal()
    save_history = pyqtSignal()
    load_history = pyqtSignal()
    start_batch = pyqtSignal()
    stop_batch = pyqtSignal()

    def __init__(self):
        """初始化批量处理控制面板"""
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 控制区域
        control_group = QGroupBox()
        control_group.setStyleSheet("border: none; margin-top: 10px;")
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Status label with styling
        self.status_label = QLabel(i18n.translate("batch_ready"))
        self.status_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                font-size: 10pt;
                padding: 6px 12px;
                background-color: #e8f5e8;
                border: 1px solid #c8e6c9;
                border-radius: 6px;
                color: #2e7d32;
            }
        """
        )
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        # Task management buttons
        task_buttons = QWidget()
        task_buttons_layout = QHBoxLayout(task_buttons)
        task_buttons_layout.setContentsMargins(0, 0, 0, 0)
        task_buttons_layout.setSpacing(8)

        self.load_tasks_button = QPushButton(i18n.translate("batch_load_tasks"))
        self.load_tasks_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        task_buttons_layout.addWidget(self.load_tasks_button)

        self.save_results_button = QPushButton(i18n.translate("batch_save_results"))
        self.save_results_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        task_buttons_layout.addWidget(self.save_results_button)

        control_layout.addWidget(task_buttons)

        # History management buttons
        history_buttons = QWidget()
        history_buttons_layout = QHBoxLayout(history_buttons)
        history_buttons_layout.setContentsMargins(0, 0, 0, 0)
        history_buttons_layout.setSpacing(8)

        self.save_history_button = QPushButton(i18n.translate("batch_save_history"))
        self.save_history_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        history_buttons_layout.addWidget(self.save_history_button)

        self.load_history_button = QPushButton(i18n.translate("batch_load_history"))
        self.load_history_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        history_buttons_layout.addWidget(self.load_history_button)

        control_layout.addWidget(history_buttons)

        # Process control buttons
        process_buttons = QWidget()
        process_buttons_layout = QHBoxLayout(process_buttons)
        process_buttons_layout.setContentsMargins(0, 0, 0, 0)
        process_buttons_layout.setSpacing(8)

        self.start_batch_button = QPushButton(i18n.translate("batch_start_processing"))
        self.start_batch_button.setStyleSheet(
            """
            QPushButton {
                padding: 9px 20px;
                border: none;
                border-radius: 6px;
                background-color: #4caf50;
                color: white;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
            }
        """
        )
        process_buttons_layout.addWidget(self.start_batch_button)

        self.stop_batch_button = QPushButton(i18n.translate("batch_stop_processing"))
        self.stop_batch_button.setEnabled(False)
        self.stop_batch_button.setStyleSheet(
            """
            QPushButton {
                padding: 9px 20px;
                border: none;
                border-radius: 6px;
                background-color: #f44336;
                color: white;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:disabled {
                background-color: #ef9a9a;
            }
        """
        )
        process_buttons_layout.addWidget(self.stop_batch_button)

        control_layout.addWidget(process_buttons)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        self.setLayout(layout)

    def update_status(self, status):
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self.status_label.setText(status)

    def set_controls_enabled(self, start_enabled, stop_enabled):
        """
        设置控制按钮的启用状态

        Args:
            start_enabled: 开始按钮是否启用
            stop_enabled: 停止按钮是否启用
        """
        self.start_batch_button.setEnabled(start_enabled)
        self.stop_batch_button.setEnabled(stop_enabled)

    def reinit_ui(self):
        """
        重新初始化UI文本，用于语言切换
        """
        # 更新所有按钮文本
        self.load_tasks_button.setText(i18n.translate("batch_load_tasks"))
        self.save_results_button.setText(i18n.translate("batch_save_results"))
        self.save_history_button.setText(i18n.translate("batch_save_history"))
        self.load_history_button.setText(i18n.translate("batch_load_history"))
        self.start_batch_button.setText(i18n.translate("batch_start_processing"))
        self.stop_batch_button.setText(i18n.translate("batch_stop_processing"))

        # 直接将状态重置为当前语言的"batch_ready"状态，不尝试匹配复杂的动态状态
        self.status_label.setText(i18n.translate("batch_ready"))
