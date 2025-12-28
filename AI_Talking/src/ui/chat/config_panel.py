# -*- coding: utf-8 -*-
"""
聊天配置面板组件，用于配置聊天参数
"""

import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
)

# 导入国际化管理器
from utils.i18n_manager import i18n


class ConfigPanel(QWidget):
    """
    聊天配置面板组件，用于配置聊天参数
    """

    def __init__(self):
        """
        初始化聊天配置面板
        """
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天配置面板UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 聊天配置区域
        chat_config_group = QGroupBox(i18n.translate("chat_config"))
        chat_config_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
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
        chat_config_layout = QHBoxLayout()
        chat_config_layout.setContentsMargins(10, 5, 10, 10)
        chat_config_layout.setSpacing(15)

        # API和模型配置行
        api_model_layout = QHBoxLayout()
        api_model_layout.setSpacing(8)

        # API选择
        api_layout = QHBoxLayout()
        api_layout.setSpacing(5)
        api_layout.addWidget(
            QLabel(i18n.translate("chat_model_provider")), alignment=Qt.AlignVCenter
        )
        self.chat_api_combo = QComboBox()
        self.chat_api_combo.addItems(["Ollama", "OpenAI", "DeepSeek", "Ollama Cloud"])
        self.chat_api_combo.setCurrentText("Ollama")  # 默认选择Ollama API
        self.chat_api_combo.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        api_layout.addWidget(self.chat_api_combo)
        api_model_layout.addLayout(api_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(5)
        model_layout.addWidget(
            QLabel(i18n.translate("chat_model")), alignment=Qt.AlignVCenter
        )
        self.chat_model_combo = QComboBox()
        self.chat_model_combo.setFixedWidth(250)
        self.chat_model_combo.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        model_layout.addWidget(self.chat_model_combo)
        api_model_layout.addLayout(model_layout)

        # 温度调节功能
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(5)
        temp_layout.addWidget(
            QLabel(i18n.translate("chat_temperature")), alignment=Qt.AlignVCenter
        )
        self.chat_temperature_spin = QDoubleSpinBox()
        self.chat_temperature_spin.setRange(0.0, 2.0)
        self.chat_temperature_spin.setSingleStep(0.1)
        self.chat_temperature_spin.setValue(0.8)  # 默认温度设置
        self.chat_temperature_spin.setToolTip(
            i18n.translate("chat_temperature_tooltip")
        )
        self.chat_temperature_spin.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        temp_layout.addWidget(self.chat_temperature_spin)
        temp_layout.addWidget(
            QLabel(i18n.translate("chat_temperature_range")), alignment=Qt.AlignVCenter
        )

        # 添加拉伸空间，将logo推到最右侧
        temp_layout.addStretch(1)

        # 添加NONEAD Logo
        # 获取当前目录
        if getattr(sys, "frozen", False):
            # 打包后的可执行文件所在目录
            current_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下的当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            current_dir = os.path.dirname(current_dir)  # 向上一级目录
            current_dir = os.path.dirname(current_dir)  # 再向上一级目录

        # 创建Logo标签
        logo_label = QLabel()
        # 使用资源管理器加载并缩放logo
        from utils.resource_manager import ResourceManager
        pixmap = ResourceManager.load_pixmap("noneadLogo.png", 200, 60)
        if pixmap:
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            # logo加载失败，显示文本标识
            logo_label.setText("NONEAD")
            logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            logo_label.setStyleSheet("color: #333;")

        # 添加logo到布局
        temp_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)

        api_model_layout.addLayout(temp_layout)

        chat_config_layout.addLayout(api_model_layout)

        chat_config_group.setLayout(chat_config_layout)
        layout.addWidget(chat_config_group)

        self.setLayout(layout)

    def get_api(self):
        """
        获取当前选择的API

        Returns:
            str: 当前选择的API
        """
        return self.chat_api_combo.currentText()

    def get_model(self):
        """
        获取当前选择的模型

        Returns:
            str: 当前选择的模型
        """
        return self.chat_model_combo.currentText()

    def get_temperature(self):
        """
        获取当前选择的温度

        Returns:
            float: 当前选择的温度
        """
        return self.chat_temperature_spin.value()

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新聊天配置组标题
        for child in self.children():
            if isinstance(child, QGroupBox):
                child.setTitle(i18n.translate("chat_config"))
                break

        # 更新所有标签文本
        from PyQt5.QtWidgets import QLabel

        labels = self.findChildren(QLabel)
        for label in labels:
            current_text = label.text()
            # 根据当前文本确定翻译键
            if (
                current_text == "Model Provider:"
                or current_text == "模型提供商:"
                or current_text == "模型提供商:"
                or current_text == "モデルプロバイダー:"
            ):
                label.setText(i18n.translate("chat_model_provider"))
            elif (
                current_text == "Model:"
                or current_text == "模型:"
                or current_text == "模型:"
                or current_text == "モデル:"
            ):
                label.setText(i18n.translate("chat_model"))
            elif (
                current_text == "Temperature:"
                or current_text == "温度:"
                or current_text == "溫度:"
                or current_text == "温度:"
                or current_text == "テンパレチャー:"
            ):
                label.setText(i18n.translate("chat_temperature"))
            elif current_text == "(0.0-2.0)":
                label.setText(i18n.translate("chat_temperature_range"))

        # 更新温度调节器的提示文本
        if hasattr(self, "chat_temperature_spin"):
            self.chat_temperature_spin.setToolTip(
                i18n.translate("chat_temperature_tooltip")
            )
