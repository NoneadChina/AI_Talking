# -*- coding: utf-8 -*-
"""
聊天输入组件，支持文本输入、文件上传和快捷键
"""

import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QFileDialog,
)

# 导入国际化管理器
from utils.i18n_manager import i18n


class ChatInputWidget(QWidget):
    """
    聊天输入组件，支持文本输入、文件上传和快捷键

    信号:
        send_message: 发送消息信号，参数为消息内容
    """

    send_message = pyqtSignal(str)

    def __init__(self):
        """
        初始化聊天输入组件
        """
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天输入UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 输入区域
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText(
            i18n.translate("chat_input_placeholder")
        )
        self.input_text_edit.setMaximumHeight(100)
        self.input_text_edit.textChanged.connect(self.update_height)
        self.input_text_edit.keyPressEvent = self.key_press_event
        self.input_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
                background-color: #ffffff;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            QTextEdit:focus {
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
                outline: none;
            }
        """
        )

        layout.addWidget(self.input_text_edit)

        # 操作栏
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        # 文件上传按钮
        self.upload_button = QPushButton(i18n.translate("upload_file"))
        self.upload_button.clicked.connect(self.upload_file)
        self.upload_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 9pt;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #bdbdbd;
            }
            QPushButton:active {
                background-color: #d5d5d5;
            }
        """
        )
        action_layout.addWidget(self.upload_button)

        action_layout.addStretch(1)

        # 发送按钮
        self.send_button = QPushButton(i18n.translate("chat_send"))
        self.send_button.clicked.connect(self.send_message_handler)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                padding: 9px 24px;
                border: none;
                border-radius: 6px;
                background-color: #4caf50;
                color: white;
                font-size: 10pt;
                font-weight: bold;
                transition: all 0.2s ease;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #43a047;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:active {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
                cursor: not-allowed;
            }
        """
        )
        action_layout.addWidget(self.send_button)

        layout.addLayout(action_layout)

        self.setLayout(layout)

    def update_height(self):
        """
        自动调整输入框高度
        """
        # 禁用固定高度限制，允许自动调整
        self.input_text_edit.setFixedHeight(0)

        content_height = self.input_text_edit.document().size().height()
        max_height = 200
        min_height = 30

        # 计算合适的高度，添加20px的内边距
        new_height = int(content_height + 20)

        if new_height < min_height:
            new_height = min_height
        elif new_height > max_height:
            new_height = max_height

        # 使用setFixedHeight来设置精确的高度
        self.input_text_edit.setFixedHeight(new_height)

    def key_press_event(self, event):
        """
        处理按键事件：回车发送，Shift+回车换行
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not (event.modifiers() & Qt.ShiftModifier):
                self.send_message_handler()
                return

        QTextEdit.keyPressEvent(self.input_text_edit, event)

    def send_message_handler(self):
        """
        处理发送消息事件
        """
        message = self.input_text_edit.toPlainText().strip()
        if message:
            self.send_message.emit(message)
            self.input_text_edit.clear()
            self.input_text_edit.setFixedHeight(30)

    def upload_file(self):
        """
        处理文件上传
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, i18n.translate("select_file"), "", "All Files (*.*)"
        )
        if file_path:
            # 这里可以添加文件上传逻辑
            self.send_message.emit(f"[文件上传] {os.path.basename(file_path)}")

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新输入框占位符
        self.input_text_edit.setPlaceholderText(
            i18n.translate("chat_input_placeholder")
        )

        # 更新按钮文本
        self.upload_button.setText(i18n.translate("upload_file"))
        self.send_button.setText(i18n.translate("chat_send"))
