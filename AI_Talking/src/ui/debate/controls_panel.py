# -*- coding: utf-8 -*-
"""
辩论控制面板组件，用于提供辩论控制按钮和状态显示
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from ui.ui_utils import get_default_styles
from utils.logger_config import get_logger
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class DebateControlsPanel(QWidget):
    """
    辩论控制面板组件

    信号:
        start_signal: 开始辩论信号
        stop_signal: 停止辩论信号
        save_history_signal: 保存历史信号
        load_history_signal: 加载历史信号
        export_pdf_signal: 导出PDF信号

    属性:
        debate_status_label: 状态标签
        debate_start_button: 开始辩论按钮
        debate_stop_button: 停止辩论按钮
        save_debate_history_button: 保存历史按钮
        load_debate_history_button: 加载历史按钮
        debate_export_pdf_button: 导出PDF按钮
    """

    # 定义信号
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    save_history_signal = pyqtSignal()
    load_history_signal = pyqtSignal()
    export_pdf_signal = pyqtSignal()

    def __init__(self):
        """初始化辩论控制面板"""
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

        # 状态标签
        self.debate_status_label = QLabel(i18n.translate("ready"))
        self.debate_status_label.setStyleSheet(self.styles["status_label"])
        layout.addWidget(self.debate_status_label)

        # 添加拉伸空间
        layout.addStretch()

        # 历史管理按钮
        history_buttons = QWidget()
        history_buttons_layout = QHBoxLayout(history_buttons)
        history_buttons_layout.setContentsMargins(0, 0, 0, 0)
        history_buttons_layout.setSpacing(8)

        # 保存历史按钮
        self.save_debate_history_button = QPushButton(i18n.translate("save_history"))
        self.save_debate_history_button.setStyleSheet(self.styles["history_button"])
        self.save_debate_history_button.clicked.connect(self.save_history_signal.emit)
        history_buttons_layout.addWidget(self.save_debate_history_button)

        # 加载历史按钮
        self.load_debate_history_button = QPushButton(i18n.translate("load_history"))
        self.load_debate_history_button.setStyleSheet(self.styles["history_button"])
        self.load_debate_history_button.clicked.connect(self.load_history_signal.emit)
        history_buttons_layout.addWidget(self.load_debate_history_button)

        # 导出PDF按钮
        self.debate_export_pdf_button = QPushButton(i18n.translate("export_pdf"))
        self.debate_export_pdf_button.setStyleSheet(self.styles["history_button"])
        self.debate_export_pdf_button.clicked.connect(self.export_pdf_signal.emit)
        history_buttons_layout.addWidget(self.debate_export_pdf_button)

        layout.addWidget(history_buttons)

        # 辩论控制按钮
        process_buttons = QWidget()
        process_buttons_layout = QHBoxLayout(process_buttons)
        process_buttons_layout.setContentsMargins(0, 0, 0, 0)
        process_buttons_layout.setSpacing(8)

        # 开始辩论按钮
        self.debate_start_button = QPushButton(i18n.translate("start_debate"))
        self.debate_start_button.setStyleSheet(self.styles["start_button"])
        self.debate_start_button.clicked.connect(self.start_signal.emit)
        process_buttons_layout.addWidget(self.debate_start_button)

        # 停止辩论按钮
        self.debate_stop_button = QPushButton(i18n.translate("stop_debate"))
        self.debate_stop_button.setStyleSheet(self.styles["stop_button"])
        self.debate_stop_button.clicked.connect(self.stop_signal.emit)
        self.debate_stop_button.setEnabled(False)  # 初始状态禁用
        process_buttons_layout.addWidget(self.debate_stop_button)

        layout.addWidget(process_buttons)

        self.setLayout(layout)

    def update_status(self, status):
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self.debate_status_label.setText(status)

    def set_controls_enabled(self, start_enabled, stop_enabled):
        """
        设置控制按钮的启用状态

        Args:
            start_enabled: 开始按钮是否启用
            stop_enabled: 停止按钮是否启用
        """
        self.debate_start_button.setEnabled(start_enabled)
        self.debate_stop_button.setEnabled(stop_enabled)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新按钮文本
        self.debate_start_button.setText(i18n.translate("start_debate"))
        self.debate_stop_button.setText(i18n.translate("stop_debate"))
        self.save_debate_history_button.setText(i18n.translate("save_history"))
        self.load_debate_history_button.setText(i18n.translate("load_history"))
        self.debate_export_pdf_button.setText(i18n.translate("export_pdf"))

        # 直接将状态重置为当前语言的"ready"状态，不尝试匹配复杂的动态状态
        self.debate_status_label.setText(i18n.translate("ready"))
