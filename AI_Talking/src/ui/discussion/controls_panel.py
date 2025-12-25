# -*- coding: utf-8 -*-"""控制面板组件，负责显示状态和控制按钮"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from ui.ui_utils import create_push_button, get_default_styles
from utils.i18n_manager import i18n


class ControlsPanel(QWidget):
    """
    控制面板组件

    信号:
        start_signal: 开始讨论信号
        stop_signal: 停止讨论信号
        save_history_signal: 保存历史信号
        load_history_signal: 加载历史信号
        export_pdf_signal: 导出PDF信号
    """

    # 定义信号
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    save_history_signal = pyqtSignal()
    load_history_signal = pyqtSignal()
    export_pdf_signal = pyqtSignal()

    def __init__(self):
        """初始化控制面板"""
        super().__init__()
        self.styles = get_default_styles()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 状态显示
        self.status_label = QLabel(i18n.translate("ready"))
        self.status_label.setStyleSheet(self.styles["status_label"])
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 历史管理按钮
        history_buttons = QWidget()
        history_buttons_layout = QHBoxLayout(history_buttons)
        history_buttons_layout.setContentsMargins(0, 0, 0, 0)
        history_buttons_layout.setSpacing(8)

        # 保存历史按钮
        self.save_history_button = create_push_button(
            i18n.translate("save_history"), self.styles["history_button"]
        )
        self.save_history_button.clicked.connect(self.save_history_signal.emit)
        history_buttons_layout.addWidget(self.save_history_button)

        # 加载历史按钮
        self.load_history_button = create_push_button(
            i18n.translate("load_history"), self.styles["history_button"]
        )
        self.load_history_button.clicked.connect(self.load_history_signal.emit)
        history_buttons_layout.addWidget(self.load_history_button)

        # 导出PDF按钮
        self.export_pdf_button = create_push_button(
            i18n.translate("export_pdf"), self.styles["history_button"]
        )
        self.export_pdf_button.clicked.connect(self.export_pdf_signal.emit)
        history_buttons_layout.addWidget(self.export_pdf_button)

        layout.addWidget(history_buttons)

        # 讨论控制按钮
        process_buttons = QWidget()
        process_buttons_layout = QHBoxLayout(process_buttons)
        process_buttons_layout.setContentsMargins(0, 0, 0, 0)
        process_buttons_layout.setSpacing(8)

        # 开始按钮
        self.start_button = create_push_button(
            i18n.translate("start_discussion"), self.styles["start_button"]
        )
        self.start_button.clicked.connect(self.start_signal.emit)
        process_buttons_layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = create_push_button(
            i18n.translate("stop_discussion"), self.styles["stop_button"]
        )
        self.stop_button.clicked.connect(self.stop_signal.emit)
        self.stop_button.setEnabled(False)
        process_buttons_layout.addWidget(self.stop_button)

        layout.addWidget(process_buttons)

        self.setLayout(layout)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 直接将状态重置为当前语言的"ready"状态，不尝试匹配复杂的动态状态
        self.status_label.setText(i18n.translate("ready"))

        # 更新按钮文本
        self.save_history_button.setText(i18n.translate("save_history"))
        self.load_history_button.setText(i18n.translate("load_history"))
        self.export_pdf_button.setText(i18n.translate("export_pdf"))
        self.start_button.setText(i18n.translate("start_discussion"))
        self.stop_button.setText(i18n.translate("stop_discussion"))

    def update_status(self, status: str):
        """更新状态信息

        Args:
            status: 状态信息
        """
        self.status_label.setText(status)

    def set_controls_enabled(self, start_enabled: bool, stop_enabled: bool):
        """设置控制按钮的启用状态

        Args:
            start_enabled: 开始按钮是否启用
            stop_enabled: 停止按钮是否启用
        """
        self.start_button.setEnabled(start_enabled)
        self.stop_button.setEnabled(stop_enabled)
