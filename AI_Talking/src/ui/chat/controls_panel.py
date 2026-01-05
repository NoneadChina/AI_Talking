# -*- coding: utf-8 -*-
"""
聊天控制面板组件，用于控制聊天功能
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton

# 导入国际化管理器
from utils.i18n_manager import i18n


class ControlsPanel(QWidget):
    """
    聊天控制面板组件，用于控制聊天功能
    """

    def __init__(self):
        """
        初始化聊天控制面板
        """
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天控制面板UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 聊天控制区域
        chat_control_group = QGroupBox(i18n.translate("chat_control"))
        chat_control_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
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
        chat_control_layout = QHBoxLayout()
        chat_control_layout.setContentsMargins(10, 5, 10, 10)
        chat_control_layout.setSpacing(10)

        # 控制按钮样式
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:focus {
                outline: none;
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
            }
        """

        # 保存历史按钮
        self.save_standard_history_button = QPushButton(
            i18n.translate("chat_save_history")
        )
        self.save_standard_history_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.save_standard_history_button)

        # 加载历史按钮
        self.load_standard_history_button = QPushButton(
            i18n.translate("chat_load_history")
        )
        self.load_standard_history_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.load_standard_history_button)

        # 导出PDF按钮
        self.export_chat_pdf_button = QPushButton(i18n.translate("chat_export_pdf"))
        self.export_chat_pdf_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.export_chat_pdf_button)

        # 清除历史按钮
        self.clear_history_button = QPushButton(i18n.translate("chat_clear_history"))
        self.clear_history_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #ffebee;
                font-size: 9pt;
                color: #c62828;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
            QPushButton:focus {
                outline: none;
                border-color: #f44336;
                box-shadow: 0 0 0 2px rgba(244, 67, 54, 0.1);
            }
        """
        )
        chat_control_layout.addWidget(self.clear_history_button)

        chat_control_layout.addStretch(1)  # 添加拉伸空间，将按钮推到左侧
        chat_control_group.setLayout(chat_control_layout)
        layout.addWidget(chat_control_group)

        self.setLayout(layout)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新聊天控制组标题
        if hasattr(self, "parentWidget") and self.parentWidget():
            group_box = self.parentWidget().findChild(QGroupBox)
            if group_box:
                group_box.setTitle(i18n.translate("chat_control"))

        # 更新所有按钮文本
        if hasattr(self, "save_standard_history_button"):
            self.save_standard_history_button.setText(
                i18n.translate("chat_save_history")
            )
        if hasattr(self, "load_standard_history_button"):
            self.load_standard_history_button.setText(
                i18n.translate("chat_load_history")
            )
        if hasattr(self, "export_chat_pdf_button"):
            self.export_chat_pdf_button.setText(i18n.translate("chat_export_pdf"))
        if hasattr(self, "clear_history_button"):
            self.clear_history_button.setText(i18n.translate("chat_clear_history"))
