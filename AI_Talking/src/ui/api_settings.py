# -*- coding: utf-8 -*-
"""
API设置窗口部件，用于配置各种AI API的连接信息和系统提示词。

该部件提供了一个界面，允许用户配置OpenAI、DeepSeek和Ollama的API设置，
以及各种系统提示词。
"""

import sys
import os
from utils.logger_config import get_logger
from utils.i18n_manager import i18n
from utils.secure_storage import encrypt_data, decrypt_data
from utils.config_manager import config_manager
from utils.model_manager import model_manager
from utils.ai_service import AIServiceFactory
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QGroupBox,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QComboBox,
    QTabWidget,
)

# 获取日志记录器
logger = get_logger(__name__)


class APISettingsWidget(QWidget):
    """
    API设置窗口部件，用于配置各种AI API的连接信息和系统提示词。

    该部件提供了一个界面，允许用户配置OpenAI、DeepSeek和Ollama的API设置，
    以及各种系统提示词。

    信号:
        settings_saved: 设置保存完成信号
    """

    # 定义信号：当设置保存完成时发出
    settings_saved = pyqtSignal()

    def __init__(self):
        """
        初始化API设置窗口。

        构建API设置界面，包括API密钥输入、Ollama URL配置和系统提示词设置。
        """
        super().__init__()
        self.init_ui()  # 初始化用户界面
        self.load_settings()  # 加载已保存的设置

    def init_ui(self):
        """
        初始化API设置界面布局和控件。

        构建API设置界面的布局，包括三个标签页：
        1. 基础设置（语言选择、翻译设置等）
        2. 模型设置（OpenAI、DeepSeek、Ollama API配置）
        3. 提示词设置（聊天、讨论、辩论系统提示词）
        4. 保存按钮
        """
        # 移除现有布局
        if self.layout() is not None:
            # 断开信号连接，防止递归调用
            if hasattr(self, "language_combo"):
                try:
                    self.language_combo.currentIndexChanged.disconnect(
                        self.on_language_changed
                    )
                except:
                    pass
            # 断开保存按钮的信号连接
            if hasattr(self, "save_button"):
                try:
                    self.save_button.clicked.disconnect(self.save_settings)
                except:
                    pass
            # 移除所有子控件
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget {
                font-size: 10pt;
            }
            QTabBar {
                font-size: 11pt;
            }
            QTabBar::tab {
                padding: 8px 20px;
                margin-right: 2px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
        """
        )

        # --- 1. 模型设置标签页 ---
        model_settings_tab = QWidget()
        model_settings_layout = QVBoxLayout(model_settings_tab)
        model_settings_layout.setContentsMargins(10, 10, 10, 10)
        model_settings_layout.setSpacing(15)

        # 界面语言设置
        self.language_group = QGroupBox(i18n.translate("setting_language"))
        self.language_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        language_layout = QHBoxLayout()
        language_layout.setSpacing(10)
        self.language_label = QLabel(i18n.translate("setting_select_language"))
        language_layout.addWidget(self.language_label, alignment=Qt.AlignVCenter)
        self.language_combo = QComboBox()
        # 获取支持的语言列表
        supported_languages = i18n.get_supported_languages()
        self.language_combo.addItems(
            [lang_name for lang_name in supported_languages.values()]
        )
        self.language_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
                min-width: 180px;
            }
        """
        )
        # 连接语言切换信号
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        self.language_group.setLayout(language_layout)
        model_settings_layout.addWidget(self.language_group)

        # 翻译模型设置
        self.translation_group = QGroupBox(i18n.translate("setting_translation_model"))
        self.translation_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        translation_layout = QVBoxLayout()
        translation_layout.setSpacing(10)

        # 服务提供商
        provider_layout = QHBoxLayout()
        provider_layout.setSpacing(10)
        self.provider_label = QLabel(i18n.translate("setting_provider"))
        provider_layout.addWidget(self.provider_label, alignment=Qt.AlignVCenter)
        self.translation_provider_combo = QComboBox()
        self.translation_provider_combo.addItems(["OpenAI", "DeepSeek", "Ollama", "Ollama Cloud"])
        self.translation_provider_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
                min-width: 180px;
            }
        """)
        # 连接服务提供商变化信号，用于更新模型列表
        self.translation_provider_combo.currentIndexChanged.connect(self.on_translation_provider_changed)
        provider_layout.addWidget(self.translation_provider_combo)
        provider_layout.addStretch()
        translation_layout.addLayout(provider_layout)

        # 翻译默认模型
        model_layout = QHBoxLayout()
        model_layout.setSpacing(10)
        self.default_model_label = QLabel(i18n.translate("setting_default_model"))
        model_layout.addWidget(self.default_model_label, alignment=Qt.AlignVCenter)
        self.translation_model_combo = QComboBox()
        self.translation_model_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
                min-width: 180px;
            }
        """)
        model_layout.addWidget(self.translation_model_combo)
        model_layout.addStretch()
        translation_layout.addLayout(model_layout)

        self.translation_group.setLayout(translation_layout)
        model_settings_layout.addWidget(self.translation_group)

        # OpenAI API设置
        self.openai_group = QGroupBox(i18n.translate("setting_openai"))
        self.openai_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        openai_layout = QVBoxLayout()
        openai_layout.setSpacing(8)

        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.Password)  # 默认隐藏密钥
        self.openai_key_edit.setPlaceholderText(
            f"{i18n.translate('setting_enter')}{i18n.translate('setting_openai')} API {i18n.translate('setting_key')}"
        )
        self.openai_key_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)

        # API密钥标签
        self.openai_key_label = QLabel(i18n.translate("setting_openai_key"))
        
        # 显示密钥复选框
        self.show_openai_key = QCheckBox(i18n.translate("setting_show_key"))
        self.show_openai_key.setStyleSheet(
            """
            QCheckBox {
                font-size: 9pt;
                margin: 5px 0;
            }
        """)
        self.show_openai_key.toggled.connect(
            lambda checked: self.openai_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        openai_layout.addWidget(self.openai_key_label)
        openai_layout.addWidget(self.openai_key_edit)
        openai_layout.addWidget(self.show_openai_key)
        self.openai_group.setLayout(openai_layout)
        model_settings_layout.addWidget(self.openai_group)

        # DeepSeek API设置
        self.deepseek_group = QGroupBox(i18n.translate("setting_deepseek"))
        self.deepseek_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        deepseek_layout = QVBoxLayout()
        deepseek_layout.setSpacing(8)

        self.deepseek_key_edit = QLineEdit()
        self.deepseek_key_edit.setEchoMode(QLineEdit.Password)  # 默认隐藏密钥
        self.deepseek_key_edit.setPlaceholderText(
            f"{i18n.translate('setting_enter')}{i18n.translate('setting_deepseek')} API {i18n.translate('setting_key')}"
        )
        self.deepseek_key_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)

        # API密钥标签
        self.deepseek_key_label = QLabel(i18n.translate("setting_deepseek_key"))
        
        # 显示密钥复选框
        self.show_deepseek_key = QCheckBox(i18n.translate("setting_show_key"))
        self.show_deepseek_key.setStyleSheet(
            """
            QCheckBox {
                font-size: 9pt;
                margin: 5px 0;
            }
        """)
        self.show_deepseek_key.toggled.connect(
            lambda checked: self.deepseek_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        deepseek_layout.addWidget(self.deepseek_key_label)
        deepseek_layout.addWidget(self.deepseek_key_edit)
        deepseek_layout.addWidget(self.show_deepseek_key)
        self.deepseek_group.setLayout(deepseek_layout)
        model_settings_layout.addWidget(self.deepseek_group)

        # Ollama Cloud API设置
        self.ollama_cloud_group = QGroupBox(i18n.translate("setting_ollama_cloud"))
        self.ollama_cloud_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """)
        ollama_cloud_layout = QVBoxLayout()
        ollama_cloud_layout.setSpacing(8)

        self.ollama_cloud_key_edit = QLineEdit()
        self.ollama_cloud_key_edit.setEchoMode(QLineEdit.Password)  # 默认隐藏密钥
        self.ollama_cloud_key_edit.setPlaceholderText(
            f"{i18n.translate('setting_enter')}{i18n.translate('setting_ollama_cloud')} API {i18n.translate('setting_key')}"
        )
        self.ollama_cloud_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)

        # API密钥标签
        self.ollama_cloud_key_label = QLabel(i18n.translate("setting_ollama_cloud_key"))
        
        # 显示密钥复选框
        self.show_ollama_cloud_key = QCheckBox(i18n.translate("setting_show_key"))
        self.show_ollama_cloud_key.setStyleSheet("""
            QCheckBox {
                font-size: 9pt;
                margin: 5px 0;
            }
        """)
        self.show_ollama_cloud_key.toggled.connect(
            lambda checked: self.ollama_cloud_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        # 基础URL
        self.ollama_cloud_url_edit = QLineEdit("https://ollama.com")
        self.ollama_cloud_url_edit.setPlaceholderText(
            f"{i18n.translate('setting_enter')}{i18n.translate('setting_ollama_cloud')} API {i18n.translate('setting_base_url')}"
        )
        self.ollama_cloud_url_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)

        # 基础URL标签
        self.ollama_cloud_url_label = QLabel(i18n.translate("setting_ollama_cloud_url"))

        ollama_cloud_layout.addWidget(self.ollama_cloud_key_label)
        ollama_cloud_layout.addWidget(self.ollama_cloud_key_edit)
        ollama_cloud_layout.addWidget(self.show_ollama_cloud_key)
        ollama_cloud_layout.addWidget(self.ollama_cloud_url_label)
        ollama_cloud_layout.addWidget(self.ollama_cloud_url_edit)
        self.ollama_cloud_group.setLayout(ollama_cloud_layout)
        model_settings_layout.addWidget(self.ollama_cloud_group)

        # Ollama API设置
        self.ollama_group = QGroupBox(i18n.translate("setting_ollama"))
        self.ollama_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        ollama_layout = QVBoxLayout()
        ollama_layout.setSpacing(8)

        self.ollama_url_edit = QLineEdit("http://localhost:11434")
        self.ollama_url_edit.setPlaceholderText(
            f"{i18n.translate('setting_enter')}{i18n.translate('setting_ollama')} API {i18n.translate('setting_base_url')}"
        )
        self.ollama_url_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)

        # API基础URL标签
        self.ollama_url_label = QLabel(i18n.translate("setting_ollama_url"))
        ollama_layout.addWidget(self.ollama_url_label)
        ollama_layout.addWidget(self.ollama_url_edit)
        self.ollama_group.setLayout(ollama_layout)
        model_settings_layout.addWidget(self.ollama_group)

        # 添加模型设置标签页
        self.tab_widget.addTab(model_settings_tab, i18n.translate("tab_settings"))

        # --- 3. 提示词设置标签页 ---
        prompt_settings_tab = QWidget()
        prompt_settings_layout = QVBoxLayout(prompt_settings_tab)
        prompt_settings_layout.setContentsMargins(10, 10, 10, 10)
        prompt_settings_layout.setSpacing(15)

        # 通用提示词样式
        prompt_edit_style = """
            QTextEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
                background-color: white;
                min-height: 80px;
            }
            QTextEdit:focus {
                border-color: #4caf50;
                outline: none;
            }
        """

        # 在提示词设置标签页内部创建子标签页
        self.prompt_subtabs = QTabWidget()
        self.prompt_subtabs.setStyleSheet(
            """
            QTabBar::tab {
                padding: 8px 15px;
                margin-right: 2px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
        """
        )

        # --- 3.1 聊天提示词子标签页 ---
        chat_prompt_tab = QWidget()
        chat_prompt_layout = QVBoxLayout(chat_prompt_tab)
        chat_prompt_layout.setContentsMargins(5, 5, 5, 5)
        chat_prompt_layout.setSpacing(15)

        # 聊天系统提示词
        self.chat_group = QGroupBox(i18n.translate("setting_chat_prompt"))
        self.chat_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        chat_layout = QVBoxLayout()
        self.chat_system_prompt_edit = QTextEdit()
        self.chat_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_chat_prompt_placeholder")
        )
        self.chat_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.chat_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        chat_layout.addWidget(self.chat_system_prompt_edit, 1)  # 添加拉伸因子
        self.chat_group.setLayout(chat_layout)
        chat_prompt_layout.addWidget(self.chat_group, 1)  # 添加拉伸因子

        # 添加聊天提示词子标签页
        self.prompt_subtabs.addTab(chat_prompt_tab, i18n.translate("tab_chat"))

        # --- 3.2 讨论提示词子标签页 ---
        discussion_prompt_tab = QWidget()
        discussion_prompt_layout = QVBoxLayout(discussion_prompt_tab)
        discussion_prompt_layout.setContentsMargins(5, 5, 5, 5)
        discussion_prompt_layout.setSpacing(15)

        # 讨论系统提示词
        self.discussion_group = QGroupBox(i18n.translate("setting_discussion_prompt"))
        self.discussion_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        discussion_layout = QVBoxLayout()
        discussion_layout.setSpacing(8)

        # 讨论共享系统提示词
        self.common_system_prompt_edit = QTextEdit()
        self.common_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_discussion_prompt_placeholder")
        )
        self.common_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.common_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.discussion_shared_prompt_label = QLabel(i18n.translate("setting_shared_prompt"))
        discussion_layout.addWidget(self.discussion_shared_prompt_label)
        discussion_layout.addWidget(self.common_system_prompt_edit, 1)  # 添加拉伸因子

        # 讨论AI1和AI2系统提示词
        discussion_ai_layout = QHBoxLayout()
        discussion_ai_layout.setSpacing(10)

        ai1_layout = QVBoxLayout()
        ai1_layout.setSpacing(5)
        self.discussion_ai1_label = QLabel(i18n.translate("setting_ai1"))
        ai1_layout.addWidget(self.discussion_ai1_label)
        self.ai1_system_prompt_edit = QTextEdit()
        self.ai1_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_discussion_ai1_placeholder")
        )
        self.ai1_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.ai1_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ai1_layout.addWidget(self.ai1_system_prompt_edit, 1)  # 添加拉伸因子
        discussion_ai_layout.addLayout(ai1_layout, 1)

        ai2_layout = QVBoxLayout()
        ai2_layout.setSpacing(5)
        self.discussion_ai2_label = QLabel(i18n.translate("setting_ai2"))
        ai2_layout.addWidget(self.discussion_ai2_label)
        self.ai2_system_prompt_edit = QTextEdit()
        self.ai2_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_discussion_ai2_placeholder")
        )
        self.ai2_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.ai2_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ai2_layout.addWidget(self.ai2_system_prompt_edit, 1)  # 添加拉伸因子
        discussion_ai_layout.addLayout(ai2_layout, 1)

        discussion_layout.addLayout(discussion_ai_layout, 1)  # 添加拉伸因子

        # 专家AI3系统提示词
        expert_layout = QVBoxLayout()
        expert_layout.setSpacing(5)
        self.expert_ai3_label = QLabel(i18n.translate("setting_expert_ai3"))
        expert_layout.addWidget(self.expert_ai3_label)
        self.expert_ai3_system_prompt_edit = QTextEdit()
        self.expert_ai3_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_expert_ai3_placeholder")
        )
        self.expert_ai3_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.expert_ai3_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        expert_layout.addWidget(self.expert_ai3_system_prompt_edit, 1)  # 添加拉伸因子
        discussion_layout.addLayout(expert_layout, 1)  # 添加拉伸因子

        self.discussion_group.setLayout(discussion_layout)
        discussion_prompt_layout.addWidget(self.discussion_group, 1)  # 添加拉伸因子

        # 添加讨论提示词子标签页
        self.prompt_subtabs.addTab(
            discussion_prompt_tab, i18n.translate("tab_discussion")
        )

        # --- 3.3 辩论提示词子标签页 ---
        debate_prompt_tab = QWidget()
        debate_prompt_layout = QVBoxLayout(debate_prompt_tab)
        debate_prompt_layout.setContentsMargins(5, 5, 5, 5)
        debate_prompt_layout.setSpacing(15)

        # 辩论系统提示词
        self.debate_group = QGroupBox(i18n.translate("setting_debate_prompt"))
        self.debate_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 5px;
                padding: 10px;
            }
        """
        )
        debate_layout = QVBoxLayout()
        debate_layout.setSpacing(8)

        # 辩论共享系统提示词
        self.debate_common_prompt_edit = QTextEdit()
        self.debate_common_prompt_edit.setPlaceholderText(
            i18n.translate("setting_debate_prompt_placeholder")
        )
        self.debate_common_prompt_edit.setStyleSheet(prompt_edit_style)
        self.debate_common_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.debate_shared_prompt_label = QLabel(i18n.translate("setting_shared_prompt"))
        debate_layout.addWidget(self.debate_shared_prompt_label)
        debate_layout.addWidget(self.debate_common_prompt_edit, 1)  # 添加拉伸因子

        # 辩论AI1和AI2系统提示词
        debate_ai_layout = QHBoxLayout()
        debate_ai_layout.setSpacing(10)

        debate_ai1_layout = QVBoxLayout()
        debate_ai1_layout.setSpacing(5)
        self.debate_ai1_label = QLabel(i18n.translate("setting_debate_ai1"))
        debate_ai1_layout.addWidget(self.debate_ai1_label)
        self.debate_ai1_prompt_edit = QTextEdit()
        self.debate_ai1_prompt_edit.setPlaceholderText(
            i18n.translate("setting_debate_ai1_placeholder")
        )
        self.debate_ai1_prompt_edit.setStyleSheet(prompt_edit_style)
        self.debate_ai1_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        debate_ai1_layout.addWidget(self.debate_ai1_prompt_edit, 1)  # 添加拉伸因子
        debate_ai_layout.addLayout(debate_ai1_layout, 1)

        debate_ai2_layout = QVBoxLayout()
        debate_ai2_layout.setSpacing(5)
        self.debate_ai2_label = QLabel(i18n.translate("setting_debate_ai2"))
        debate_ai2_layout.addWidget(self.debate_ai2_label)
        self.debate_ai2_prompt_edit = QTextEdit()
        self.debate_ai2_prompt_edit.setPlaceholderText(
            i18n.translate("setting_debate_ai2_placeholder")
        )
        self.debate_ai2_prompt_edit.setStyleSheet(prompt_edit_style)
        self.debate_ai2_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        debate_ai2_layout.addWidget(self.debate_ai2_prompt_edit, 1)  # 添加拉伸因子
        debate_ai_layout.addLayout(debate_ai2_layout, 1)

        debate_layout.addLayout(debate_ai_layout, 1)  # 添加拉伸因子

        # 裁判AI3系统提示词
        judge_layout = QVBoxLayout()
        judge_layout.setSpacing(5)
        self.judge_ai3_label = QLabel(i18n.translate("setting_judge_ai3"))
        judge_layout.addWidget(self.judge_ai3_label)
        self.judge_ai3_system_prompt_edit = QTextEdit()
        self.judge_ai3_system_prompt_edit.setPlaceholderText(
            i18n.translate("setting_judge_ai3_placeholder")
        )
        self.judge_ai3_system_prompt_edit.setStyleSheet(prompt_edit_style)
        self.judge_ai3_system_prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        judge_layout.addWidget(self.judge_ai3_system_prompt_edit, 1)  # 添加拉伸因子
        debate_layout.addLayout(judge_layout, 1)  # 添加拉伸因子

        self.debate_group.setLayout(debate_layout)
        debate_prompt_layout.addWidget(self.debate_group, 1)  # 添加拉伸因子

        # 添加辩论提示词子标签页
        self.prompt_subtabs.addTab(debate_prompt_tab, i18n.translate("tab_debate"))

        # 将子标签页添加到提示词设置标签页的布局中
        prompt_settings_layout.addWidget(self.prompt_subtabs, 1)  # 添加拉伸因子

        # 添加提示词设置标签页
        self.tab_widget.addTab(prompt_settings_tab, i18n.translate("setting_prompt"))

        # 保存按钮
        self.save_button = QPushButton(i18n.translate("setting_save"))
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet(
            """
            QPushButton {
                padding: 10px 20px;
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """
        )

        # 将标签页和保存按钮添加到主布局
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.save_button, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def on_language_changed(self, index):
        """
        语言选择变化时的处理函数

        Args:
            index: 当前选择的语言索引
        """
        # 获取当前选择的语言代码
        lang_name = self.language_combo.itemText(index)
        supported_languages = i18n.get_supported_languages()
        # 查找对应的语言代码
        lang_code = None
        for code, name in supported_languages.items():
            if name == lang_name:
                lang_code = code
                break

        if lang_code:
            # 先断开信号连接，防止递归调用
            self.language_combo.currentIndexChanged.disconnect(self.on_language_changed)

            try:
                # 先保存设置，确保环境变量被更新
                # 但不弹出消息框，由language_changed信号的处理函数统一处理
                # 语言切换时不显示确认对话框
                self.save_settings(show_message=False, show_confirm=False)
                # 设置当前语言 - 这会自动发出language_changed信号，触发所有组件的reinit_ui
                i18n.set_language(lang_code)
                # 不再需要手动调用reinit_ui，因为language_changed信号会自动触发
            finally:
                # 重新连接信号
                self.language_combo.currentIndexChanged.connect(
                    self.on_language_changed
                )

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新所有文本控件的翻译
        # 语言设置组
        if hasattr(self, "language_group"):
            self.language_group.setTitle(i18n.translate("setting_language"))
        if hasattr(self, "language_label"):
            self.language_label.setText(i18n.translate("setting_select_language"))

        # 翻译模型设置组
        if hasattr(self, "translation_group"):
            self.translation_group.setTitle(i18n.translate("setting_translation_model"))
        if hasattr(self, "provider_label"):
            self.provider_label.setText(i18n.translate("setting_provider"))
        if hasattr(self, "default_model_label"):
            self.default_model_label.setText(i18n.translate("setting_default_model"))

        # OpenAI API设置组
        if hasattr(self, "openai_group"):
            self.openai_group.setTitle(i18n.translate("setting_openai"))
        if hasattr(self, "openai_key_label"):
            self.openai_key_label.setText(i18n.translate("setting_openai_key"))
        if hasattr(self, "show_openai_key"):
            self.show_openai_key.setText(i18n.translate("setting_show_key"))
        if hasattr(self, "openai_key_edit"):
            self.openai_key_edit.setPlaceholderText(
                f"{i18n.translate('setting_enter')}{i18n.translate('setting_openai')} API {i18n.translate('setting_key')}"
            )

        # DeepSeek API设置组
        if hasattr(self, "deepseek_group"):
            self.deepseek_group.setTitle(i18n.translate("setting_deepseek"))
        if hasattr(self, "deepseek_key_label"):
            self.deepseek_key_label.setText(i18n.translate("setting_deepseek_key"))
        if hasattr(self, "show_deepseek_key"):
            self.show_deepseek_key.setText(i18n.translate("setting_show_key"))
        if hasattr(self, "deepseek_key_edit"):
            self.deepseek_key_edit.setPlaceholderText(
                f"{i18n.translate('setting_enter')}{i18n.translate('setting_deepseek')} API {i18n.translate('setting_key')}"
            )

        # Ollama Cloud API设置组
        if hasattr(self, "ollama_cloud_group"):
            self.ollama_cloud_group.setTitle(i18n.translate("setting_ollama_cloud"))
        if hasattr(self, "ollama_cloud_key_label"):
            self.ollama_cloud_key_label.setText(i18n.translate("setting_ollama_cloud_key"))
        if hasattr(self, "show_ollama_cloud_key"):
            self.show_ollama_cloud_key.setText(i18n.translate("setting_show_key"))
        if hasattr(self, "ollama_cloud_key_edit"):
            self.ollama_cloud_key_edit.setPlaceholderText(
                f"{i18n.translate('setting_enter')}{i18n.translate('setting_ollama_cloud')} API {i18n.translate('setting_key')}"
            )

        # Ollama API设置组
        if hasattr(self, "ollama_group"):
            self.ollama_group.setTitle(i18n.translate("setting_ollama"))
        if hasattr(self, "ollama_url_label"):
            self.ollama_url_label.setText(i18n.translate("setting_ollama_url"))
        if hasattr(self, "ollama_url_edit"):
            self.ollama_url_edit.setPlaceholderText(
                f"{i18n.translate('setting_enter')}{i18n.translate('setting_ollama')} API {i18n.translate('setting_base_url')}"
            )

        # 保存按钮
        if hasattr(self, "save_button"):
            self.save_button.setText(i18n.translate("setting_save"))

        # 标签页标题
        if hasattr(self, "tab_widget"):
            self.tab_widget.setTabText(0, i18n.translate("tab_settings"))
            self.tab_widget.setTabText(1, i18n.translate("setting_prompt"))

        # 提示词子标签页标题
        if hasattr(self, "prompt_subtabs"):
            self.prompt_subtabs.setTabText(0, i18n.translate("tab_chat"))
            self.prompt_subtabs.setTabText(1, i18n.translate("tab_discussion"))
            self.prompt_subtabs.setTabText(2, i18n.translate("tab_debate"))

        # 聊天提示词组
        if hasattr(self, "chat_group"):
            self.chat_group.setTitle(i18n.translate("setting_chat_prompt"))
            self.chat_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_chat_prompt_placeholder")
            )

        # 讨论提示词组
        if hasattr(self, "discussion_group"):
            self.discussion_group.setTitle(i18n.translate("setting_discussion_prompt"))
            if hasattr(self, "discussion_shared_prompt_label"):
                self.discussion_shared_prompt_label.setText(i18n.translate("setting_shared_prompt"))
            if hasattr(self, "discussion_ai1_label"):
                self.discussion_ai1_label.setText(i18n.translate("setting_ai1"))
            if hasattr(self, "discussion_ai2_label"):
                self.discussion_ai2_label.setText(i18n.translate("setting_ai2"))
            if hasattr(self, "expert_ai3_label"):
                self.expert_ai3_label.setText(i18n.translate("setting_expert_ai3"))
            self.common_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_discussion_prompt_placeholder")
            )
            self.ai1_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_discussion_ai1_placeholder")
            )
            self.ai2_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_discussion_ai2_placeholder")
            )
            self.expert_ai3_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_expert_ai3_placeholder")
            )

        # 辩论提示词组
        if hasattr(self, "debate_group"):
            self.debate_group.setTitle(i18n.translate("setting_debate_prompt"))
            if hasattr(self, "debate_shared_prompt_label"):
                self.debate_shared_prompt_label.setText(i18n.translate("setting_shared_prompt"))
            if hasattr(self, "debate_ai1_label"):
                self.debate_ai1_label.setText(i18n.translate("setting_debate_ai1"))
            if hasattr(self, "debate_ai2_label"):
                self.debate_ai2_label.setText(i18n.translate("setting_debate_ai2"))
            if hasattr(self, "judge_ai3_label"):
                self.judge_ai3_label.setText(i18n.translate("setting_judge_ai3"))
            self.debate_common_prompt_edit.setPlaceholderText(
                i18n.translate("setting_debate_prompt_placeholder")
            )
            self.debate_ai1_prompt_edit.setPlaceholderText(
                i18n.translate("setting_debate_ai1_placeholder")
            )
            self.debate_ai2_prompt_edit.setPlaceholderText(
                i18n.translate("setting_debate_ai2_placeholder")
            )
            self.judge_ai3_system_prompt_edit.setPlaceholderText(
                i18n.translate("setting_judge_ai3_placeholder")
            )

    def load_settings(self):
        """
        加载现有的API设置。

        从配置文件中读取之前保存的配置信息并填充到表单中，包括：
        1. API密钥
        2. Ollama URL
        3. 系统提示词
        """
        # 加载API密钥和URL - 解密密钥
        from utils.secure_storage import decrypt_data
        # 从配置管理器获取API设置
        self.openai_key_edit.setText(decrypt_data(config_manager.get('api.openai_key', '')))
        self.deepseek_key_edit.setText(decrypt_data(config_manager.get('api.deepseek_key', '')))
        self.ollama_cloud_key_edit.setText(decrypt_data(config_manager.get('api.ollama_cloud_key', '')))
        self.ollama_cloud_url_edit.setText(config_manager.get('api.ollama_cloud_base_url', 'https://ollama.com'))
        self.ollama_url_edit.setText(config_manager.get('api.ollama_base_url', 'http://localhost:11434'))
        
        # 加载翻译设置
        translation_provider = config_manager.get('translation.provider', 'Ollama')
        self.translation_provider = translation_provider
        translation_model = config_manager.get('translation.default_model', 'llama3')
        
        # 设置服务提供商
        index = self.translation_provider_combo.findText(translation_provider)
        if index >= 0:
            self.translation_provider_combo.setCurrentIndex(index)
        
        # 初始化模型列表
        self.on_translation_provider_changed(index)
        
        # 设置默认模型
        index = self.translation_model_combo.findText(translation_model)
        if index >= 0:
            self.translation_model_combo.setCurrentIndex(index)

        # 加载系统提示词
        # 聊天系统提示词
        default_chat_prompt = "角色定位\n你是一位专业、友善且知识渊博的智能助手，名为“智言”。\n## 核心原则\n1. 准确性第一：基于事实和可靠信息回答，不确定时明确说明\n2. 完整性：提供充分的信息和背景，但避免冗余\n3. 清晰易懂：用平实的简体中文表达，复杂概念需解释\n4. 实用性：回答应具有实际应用价值或启发意义\n## 回答规范\n### 信息类问题回答框架\n1. 核心答案：首先直接、明确地回答核心问题\n2. 关键细节：提供必要的背景信息、数据或定义\n3. 应用场景：说明该信息在现实中的应用或意义\n4. 注意事项：如有需要，补充相关限制条件或争议点\n5. 延伸建议：根据问题性质，提供进一步探索的方向\n### 咨询建议类问题回答框架\n1. 问题分析：简要分析问题的核心矛盾或需求\n2. 方案提供：给出具体、可操作的解决方案或建议\n3. 优劣分析：客观分析不同方案的优缺点\n4. 实施步骤：如适用，提供分步指导\n5. 风险提示：提醒潜在风险或注意事项\n### 创意类问题回答框架\n1. 创意发散：提供多种可能性或思路\n2. 结构组织：帮助整理创意的逻辑框架\n3. 评估标准：提供评估创意质量的标准\n4. 优化建议：给出进一步完善的方向\n## 语言与表达要求\n### 语言规范\n- 使用标准简体中文\n- 专业术语初次出现时需解释\n- 避免网络流行语和不规范表达\n- 句子结构完整，标点正确\n### 语气与态度\n- 保持友善、耐心、专业\n- 尊重用户，不评判用户问题本身\n- 鼓励探索和思考\n- 热情但不夸张\n### 格式规范\n- 较长的回答使用段落分隔\n- 列表项使用数字或项目符号\n- 重要概念可使用强调\n- 复杂信息可考虑表格呈现\n## 特殊情况处理\n### 知识边界处理\n- 如果问题超出知识范围，诚实说明\n- 提供可能的替代信息源或搜索方向\n- 区分“不知道”和“无法确定”\n### 敏感问题处理\n- 不提供违反法律、伦理的建议\n- 对争议性问题保持客观中立\n- 如有必要，提供多视角分析\n### 复杂问题处理\n- 分步骤解答\n- 提供思维框架而非简单答案\n- 鼓励用户参与思考过程\n## 优秀回答标准\n1. 精准性：准确命中问题核心\n2. 深度：不止于表面，提供深入见解\n3. 结构：逻辑清晰，层次分明\n4. 实用：具有实际应用价值\n5. 启发：激发进一步思考\n## 响应模板示例\n### 信息确认型\n“关于[问题主题]，我的理解是...。具体来说...”\n### 建议提供型\n“针对您提到的[问题描述]，我建议可以从以下几个方面考虑：1... 2... 3...”\n### 复杂解释型\n“这个问题涉及几个关键概念，我们先从最基本的开始：[概念A]是指...，然后我们再来看...”\n### 知识边界型\n“关于[具体问题]，我的知识库中相关信息有限。不过，我可以为您提供相关的思考框架...”\n## 持续优化机制\n- 主动询问回答是否满足需求\n- 鼓励用户提供反馈\n- 根据上下文调整回答深度\n- 记住对话历史中的重要偏好\n---\n现在，我已经准备好为您提供准确、有用的信息。请问有什么可以帮助您的吗？\n注意：系统将始终使用简体中文回复，确保所有回答符合中文表达习惯和规范。"
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        chat_prompt = config_manager.get('chat.system_prompt', '')
        if not chat_prompt:
            chat_prompt = default_chat_prompt
        self.chat_system_prompt_edit.setPlainText(chat_prompt)

        # 讨论共享系统提示词
        default_common_prompt = "你是一个严谨的学者，正在进行一场基于第一性原理的学术讨论，讨论主题{topic}。请遵循以下原则：\n### 核心原则\n1. 第一性原理思维：始终从最基本的公理、定律或事实出发进行推导，避免依赖类比或经验假设\n2. 渐进深入：从浅层现象逐步推导到深层原理，每一步推理需有逻辑支撑\n3. 对话连续性：认真回应对手的观点，可赞同补充或理性反驳，形成真正的思想交锋\n### 讨论流程规范\n1. 起始层（首轮）：明确讨论主题的基本定义、范围和相关基础事实\n2. 推导层：通过逻辑推演分析因果关系、约束条件与可能性\n3. 深化层：探讨底层机制、本质规律与跨领域关联\n4. 收敛层：识别共识点与分歧点，明确待验证的假设\n### 表达要求\n- 语言保持学术严谨，但避免过度专业化以便理解\n- 每个论点需提供推理路径，使用“因为…所以…”“基于…可推导…”等逻辑连接\n- 当遇到不确定时，可明确标注“此为假设需验证”\n### 对话纪律\n- 每次发言聚焦1-2个核心点，深度优于广度\n- 禁止重复已陈述内容，禁止脱离主题的延伸\n- 若对方提出有效反证，应调整或放弃原有观点。"
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        common_prompt = config_manager.get('discussion.system_prompt', '')
        if not common_prompt:
            common_prompt = default_common_prompt
        self.common_system_prompt_edit.setPlainText(common_prompt)

        # 讨论AI1系统提示词
        default_ai1_prompt = '角色设定\n你是分析型学者A，擅长解构问题并建立理论框架。你的思维特点是：\n### 思维倾向\n1. 结构优先：习惯先将问题分解为基本要素，建立分析框架\n2. 原理追溯：偏好追问“为什么成立”而非“如何应用”\n3. 边界敏感：关注理论的前提条件和适用范围\n### 特殊职责\n1. 讨论发起：在首轮对话中，你需：\n - 明确定义讨论主题的核心概念\n - 列出已知的基本事实或公理\n - 提出初始分析框架\n2. 逻辑监督：在讨论中注意：\n - 指出逻辑链条的缺失环节\n - 提醒论证过程中的隐含假设\n - 标记需要验证的推论\n### 表达特征\n- 常用表述：让我们先厘清…/从最基本层面看…/这个结论依赖于三个前提…\n- 适度使用思维导图式列举（如 第一、第二、第三 ）\n- 在对方提出案例时，尝试将其归纳为一般规律'
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        ai1_prompt = config_manager.get('discussion.ai1_prompt', '')
        if not ai1_prompt:
            ai1_prompt = default_ai1_prompt
        self.ai1_system_prompt_edit.setPlainText(ai1_prompt)

        # 讨论AI2系统提示词
        default_ai2_prompt = '角色设定\n你是综合型学者B，擅长连接多元视角并检验理论适用性。你的思维特点是：\n### 思维倾向\n1. 关联思维：善于发现不同领域的相似模式或原理\n2. 实证导向：关注理论在现实场景中的解释力与预测力\n3. 系统思考：偏好考察各要素的相互作用与整体涌现性\n### 特殊职责\n1. 视角拓展：在讨论中需：\n - 提供跨领域类比或反例\n - 检验理论在不同情境下的稳健性\n - 提出“如果…会怎样”的探索性问题\n2. 实践锚定：\n - 将抽象原理与具体现象连接\n - 指出理论应用的潜在挑战\n - 评估推导结果的现实意义\n### 表达特征\n- 常用表述 这个原理在X领域也表现为…/如果换个情境…/实际案例显示…/\n- 擅长使用 另一方面…  值得注意的是…进行视角补充\n- 当对方提出框架时，尝试为其寻找边界案例或例外情况'
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        ai2_prompt = config_manager.get('discussion.ai2_prompt', '')
        if not ai2_prompt:
            ai2_prompt = default_ai2_prompt
        self.ai2_system_prompt_edit.setPlainText(ai2_prompt)

        # 专家AI3系统提示词
        default_expert_ai3_prompt = "角色设定\n你是领域专家，负责对学术讨论进行系统性总结与提炼,讨论主题{topic}。\n### 总结框架\n请按以下结构组织总结报告：\n#### 1. 讨论演进图谱\n- 标注关键转折点：何时/如何从表层进入深层讨论\n- 绘制逻辑演进路线：展示核心观点的推导路径\n- 识别突破性见解：标记最具启发性的推理环节\n#### 2. 共识与分歧矩阵\n- 共识基础：双方完全认同的基本原理与事实\n- 建设性分歧：促进讨论深度的关键争议点\n- 未决问题：受限于当前信息未能解决的疑问\n#### 3. 第一性原理追溯\n- 回溯每个重要结论的原始出发点\n- 验证推导过程中是否存在逻辑跳跃\n- 标注仍依赖于经验假设的环节\n#### 4. 用户价值提炼\n- 根据用户需求（需在总结前明确），定向提取：\n - 若用户需要决策支持：提取可操作原则与风险评估\n - 若用户需要知识理解：构建概念层级与关系图谱\n - 若用户需要创新启发：识别跨界连接点与未探索方向\n#### 5. 后续探索建议\n- 提出2-3个可深化研究的方向\n- 推荐关键验证方法或数据来源\n- 提示潜在认知盲区或风险\n### 表达要求\n- 使用专家级但易懂的语言，避免简单复述对话\n- 重要结论需标注其可靠性等级（高/中/低）\n- 可选择性使用表格、流程图等可视化思维工具\n- 最终提供一份可供用户直接使用的知识成果"
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        expert_ai3_prompt = config_manager.get('discussion.expert_ai3_prompt', '')
        if not expert_ai3_prompt:
            expert_ai3_prompt = default_expert_ai3_prompt
        self.expert_ai3_system_prompt_edit.setPlainText(expert_ai3_prompt)

        # 加载辩论系统提示词
        # 辩论共享系统提示词
        default_debate_common_prompt = '角色与原则\n你是一位专业的辩论选手，参与一场结构化的深度辩论，辩论主题"{topic}"。请遵循以下核心原则：\n### 辩论基础规范\n1. 逻辑优先原则：以逻辑推演为核心，情感与修辞为辅\n2. 事实为本原则：论点需有事实或数据支持，避免纯粹主观臆断\n3. 渐进深入原则：从表层论点逐步深入核心矛盾，展现思维深度\n4. 针对回应对手原则：每轮发言必须回应对方的核心质疑或论点\n### 辩论阶段指引\n阶段一（第1-2轮）：立论与初步交锋\n- 清晰陈述己方核心立场与主要论点\n- 提供支撑论点的基本事实与逻辑\n- 初步质疑对方立场的基础合理性\n阶段二（第3-5轮）：深度攻防\n- 深入剖析对方论证的潜在矛盾\n- 防御己方论点的薄弱环节\n- 引入更复杂的现实案例或理论依据\n- 识别并攻击对方逻辑链条的关键节点\n阶段三（第6-7轮）：总结升华\n- 系统化梳理己方论证体系\n- 揭示对方论证的根本性缺陷\n- 将辩论提升至更宏观的价值或原则层面\n- 但避免引入全新论点（可深化已有论点）\n### 辩论礼仪与禁忌\n- 可激烈交锋，但保持专业态度，避免人身攻击\n- 承认对方合理论点，展现思辨风度\n- 禁止故意曲解对方观点\n- 避免循环论证或重复相同论点\n- 当数据不确定时，明确标注“假设”“推测”等限定词\n### 发言结构建议（非强制）\n1. 回应对手上轮关键质疑（如有）\n2. 陈述本轮核心论点（1-2个）\n3. 提供论据与逻辑推演\n4. 针对对方弱点提出新质疑\n5. 简要总结本轮立场'
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        debate_common_prompt = config_manager.get('debate.system_prompt', '')
        if not debate_common_prompt:
            debate_common_prompt = default_debate_common_prompt
        self.debate_common_prompt_edit.setPlainText(debate_common_prompt)

        # 正方辩手AI1系统提示词
        default_debate_ai1_prompt = '你是正方辩手，构建一个完整、稳固、有吸引力的体系（己方立场）。建立并捍卫一个完整的论证体系。 "为什么这个观点是成立的？" 需要主动提供理由。给出一个有利于本方论证且公允、有说服力的定义，作为大厦的基石。论点之间要相互支撑，形成闭环。讲一个"好故事"。设立一个评判胜负的尺度（如"何者更有利于公平"），并证明己方完全符合。通过描绘美好愿景（采纳我方立场后的积极世界）来引发共鸣。归纳法（用多个例子证明规律）、演绎法（用公认原理推导个案）、价值升华。第一次回答不做回应反方质疑。'
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        debate_ai1_prompt = config_manager.get('debate.ai1_prompt', '')
        if not debate_ai1_prompt:
            debate_ai1_prompt = default_debate_ai1_prompt
        self.debate_ai1_prompt_edit.setPlainText(debate_ai1_prompt)

        # 反方辩手AI2系统提示词
        default_debate_ai2_prompt = '角色定位\n你是反方辩手，坚决质疑“{topic}”立场的合理性、可行性或道德性。\n### 核心思维框架\n1. 批判性思维：专注于解构对方论证的漏洞与矛盾\n2. 风险导向：强调对方立场隐含的风险、代价与不确定性\n3. 现实约束思维：突出理想与现实的差距，关注实施障碍\n4. 保守渐进主义：偏好现有方案或更稳妥的替代方案\n### 特殊策略指导\n1. 立论策略：\n - 重新定义讨论框架，强调被忽视的风险维度\n - 采用“魔鬼代言人”视角，揭示潜在意外后果\n - 建立“理想vs现实”的对比分析框架\n2. 进攻策略：\n - 重点攻击正方立场的“理想化假设”与“未证实效用”\n - 质疑正方数据的代表性或解读方式\n - 用“特例反证”瓦解正方普遍性主张\n3. 防御策略：\n - 强调“批判不等于反对，而是为了完善”\n - 提供“更优替代方案”而非单纯否定\n - 采用“即便...也不能证明...”的逻辑切割技巧\n### 表达特征\n- 常用表述：“这种观点忽略了...”“现实情况往往更复杂...”“让我们审视其潜在成本...”\n- 善用“警示性案例”与“意外后果分析”\n- 数据呈现时强调不确定性、局限性\n- 在反驳时可采用“您的前提假设存在问题，因为...”的根源性质疑技巧'
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        debate_ai2_prompt = config_manager.get('debate.ai2_prompt', '')
        if not debate_ai2_prompt:
            debate_ai2_prompt = default_debate_ai2_prompt
        self.debate_ai2_prompt_edit.setPlainText(debate_ai2_prompt)

        # 裁判AI3系统提示词
        default_judge_ai3_prompt = "角色与任务\n你是一名专业的辩论裁判AI，负责对正方AI1与反方AI2的多轮辩论进行系统分析。辩论主题为“{topic}”。\n### 裁判原则\n1. 绝对中立：避免对议题本身的预设立场，仅评价辩论过程\n2. 逻辑至上：关注论证质量而非情感强度或语言华丽度\n3. 证据优先：重视事实依据与数据支持，对模糊主张采取“不利推定”\n4. 整体评价：综合考察辩论全程表现，而非单轮胜负\n### 裁判执行流程\n第一步：多轮论述分析\n逐轮梳理双方论点，标注：\n- 逻辑链完整性（前提→推理→结论）\n- 证据强度（事实/数据/权威来源）\n- 反驳效果（是否直接回应对手质疑）\n- 识别逻辑谬误（如稻草人、滑坡、虚假两难等）\n- 标注事实性错误（如有）\n评估论述的连贯性、深度与创新性。\n第二步：评分体系（满分100分）\n评分由以下维度构成：\n1. 论证力（30分）\n- 论据的可靠性与相关性（10分）\n- 逻辑严谨性与反驳有效性（10分）\n- 论点深度与创新性（10分）\n2. 结构性与清晰度（20分）\n- 论述层次与框架清晰度（10分）\n- 语言表达与重点突出（10分）\n3. 说服力与针对性（30分）\n- 对对方弱点的攻击效果（10分）\n- 己方观点的防守稳固性（10分）\n- 整体说服力与听众导向（10分）\n4. 事实与伦理基础（20分）\n- 事实准确性及数据支持（10分）\n- 论证的伦理合理性与价值观一致性（10分）\n第三步：胜负裁决标准\n1. 胜利方判定：综合评分更高的一方获胜。\n2. 平局处理：若分差＜5分，则基于“关键回合制胜”原则裁决（即某一轮中一方取得压倒性优势）。\n3. 必须明确说明：\n - 胜利方的核心优势（如逻辑碾压、证据充分、防守稳固等）\n - 失败方的关键短板（如逻辑漏洞、回避问题、证据薄弱等）\n### 输出格式要求\n请严格按以下结构输出：\n【辩论总结】\n1. 正方核心论点（简要列举）\n2. 反方核心论点（简要列举）\n3. 关键交锋点分析（分析2-3个最激烈的争议点）\n【评分详情】\n正方AI1得分：XX/100\n- 论证力：X/30\n （论据可靠性与相关性：X/10；逻辑严谨性与反驳有效性：X/10；论点深度与创新性：X/10）\n- 结构性与清晰度：X/20\n （论述层次与框架清晰度：X/10；语言表达与重点突出：X/10）\n- 说服力与针对性：X/30\n （攻击效果：X/10；防守稳固性：X/10；整体说服力：X/10）\n- 事实与伦理基础：X/20\n （事实准确性：X/10；伦理合理性：X/10）\n反方AI2得分：XX/100\n- 论证力：X/30\n （论据可靠性与相关性：X/10；逻辑严谨性与反驳有效性：X/10；论点深度与创新性：X/10）\n- 结构性与清晰度：X/20\n （论述层次与框架清晰度：X/10；语言表达与重点突出：X/10）\n- 说服力与针对性：X/30\n （攻击效果：X/10；防守稳固性：X/10；整体说服力：X/10）\n- 事实与伦理基础：X/20\n （事实准确性：X/10；伦理合理性：X/10）\n【最终裁决】\n胜利方：[正方/反方]\n胜利理由：（结合评分维度具体说明，不少于100字）\n失败原因：（指出关键失误或不足，不少于80字）\n### 特别提醒\n- 请确保评分与文字分析的一致性\n- 避免使用模糊评价，提供具体例证\n- 如发现明显事实错误，应在分析中明确指出并影响评分\n- 伦理合理性评价需考虑普遍接受的价值原则，而非个人偏好。"
        # 从配置管理器获取提示词，如果配置管理器中没有，则使用默认值
        judge_ai3_prompt = config_manager.get('debate.judge_ai3_prompt', '')
        if not judge_ai3_prompt:
            judge_ai3_prompt = default_judge_ai3_prompt
        self.judge_ai3_system_prompt_edit.setPlainText(judge_ai3_prompt)

        # 加载语言选择设置
        self.language_combo.setCurrentText(config_manager.get('language.selection', '简体中文'))

        # 加载翻译设置
        self.translation_provider_combo.setCurrentText(
            config_manager.get('translation.provider', 'openai')
        )
        self.translation_model_combo.setCurrentText(
            config_manager.get('translation.default_model', 'gpt-4o')
        )

    def get_ollama_base_url(self):
        """获取当前设置的Ollama基础URL

        Returns:
            str: 当前配置的Ollama API基础URL
        """
        return self.ollama_url_edit.text().strip()

    def get_openai_api_key(self):
        """获取当前设置的OpenAI API密钥

        Returns:
            str: 当前配置的OpenAI API密钥
        """
        return self.openai_key_edit.text().strip()

    def get_deepseek_api_key(self):
        """获取当前设置的DeepSeek API密钥

        Returns:
            str: 当前配置的DeepSeek API密钥
        """
        return self.deepseek_key_edit.text().strip()

    def get_ollama_cloud_api_key(self):
        """获取当前设置的Ollama Cloud API密钥

        Returns:
            str: 当前配置的Ollama Cloud API密钥
        """
        return self.ollama_cloud_key_edit.text().strip()

    def get_ollama_cloud_base_url(self):
        """获取当前设置的Ollama Cloud基础URL

        Returns:
            str: 当前配置的Ollama Cloud API基础URL
        """
        return self.ollama_cloud_url_edit.text().strip()
    
    def on_translation_provider_changed(self, index):
        """翻译服务提供商变化时更新模型列表
        
        Args:
            index: 当前选择的服务提供商索引
        """
        # 获取当前选择的服务提供商
        provider = self.translation_provider_combo.currentText()
        self.translation_provider = provider
        
        # 清空当前模型列表
        self.translation_model_combo.clear()
        
        # 根据服务提供商获取模型列表
        if provider == "OpenAI":
            # 使用OpenAI的模型列表
            models = ["gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]
        elif provider == "DeepSeek":
            # 使用DeepSeek的模型列表
            models = ["deepseek-chat", "deepseek-coder-v2", "deepseek-llm-7b-chat"]
        elif provider == "Ollama":
            # 获取Ollama模型列表
            ollama_url = config_manager.get('api.ollama_base_url', 'http://localhost:11434')
            try:
                models = model_manager.get_ollama_models(ollama_url)
                if not models:
                    models = ["llama3", "phi3", "mistral", "gemma"]
            except Exception as e:
                logger.error(f"获取Ollama模型列表失败: {e}")
                models = ["llama3", "phi3", "mistral", "gemma"]
        elif provider == "Ollama Cloud":
            # 获取Ollama Cloud模型列表
            try:
                models = model_manager.get_ollama_cloud_models()
                if not models:
                    models = ["deepseek-v3.1:671b-cloud", "deepseek-v3.2:cloud", "gpt-oss:120b-cloud"]
            except Exception as e:
                logger.error(f"获取Ollama Cloud模型列表失败: {e}")
                models = ["deepseek-v3.1:671b-cloud", "deepseek-v3.2:cloud", "gpt-oss:120b-cloud"]
        else:
            models = []
        
        # 添加模型到下拉框
        self.translation_model_combo.addItems(models)
        
        # 如果有模型，选择第一个
        if models:
            self.translation_model_combo.setCurrentIndex(0)

    def save_settings(self, show_message=True, show_confirm=True):
        """
        保存API设置到配置文件。

        将用户在界面上配置的API密钥、Ollama URL和系统提示词保存到配置文件中。

        Args:
            show_message: 是否显示保存成功的消息框，默认为True
            show_confirm: 是否显示确认保存的对话框，默认为True

        Returns:
            bool: 设置保存成功返回True，失败返回False
        """
        # 只在需要时显示二次确认对话框
        if show_confirm:
            reply = QMessageBox.question(
                self,
                i18n.translate("confirm_save"),
                i18n.translate("confirm_save_msg"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                # 用户取消了保存操作
                return False

        try:
            # 更新OpenAI API密钥配置 - 始终更新，无论是否为空
            openai_key = self.openai_key_edit.text().strip()
            config_manager.set('api.openai_key', encrypt_data(openai_key) if openai_key else '')

            # 更新DeepSeek API密钥配置 - 始终更新，无论是否为空
            deepseek_key = self.deepseek_key_edit.text().strip()
            config_manager.set('api.deepseek_key', encrypt_data(deepseek_key) if deepseek_key else '')

            # 更新Ollama Cloud API密钥配置 - 始终更新，无论是否为空
            ollama_cloud_key = self.ollama_cloud_key_edit.text().strip()
            ollama_cloud_url = self.ollama_cloud_url_edit.text().strip()
            config_manager.set('api.ollama_cloud_key', encrypt_data(ollama_cloud_key) if ollama_cloud_key else '')
            config_manager.set('api.ollama_cloud_base_url', ollama_cloud_url if ollama_cloud_url else 'https://ollama.com')

            # 更新Ollama API URL配置
            ollama_url = self.ollama_url_edit.text().strip()
            if ollama_url:
                # 验证URL格式是否基本有效
                if not (
                    ollama_url.startswith("http://")
                    or ollama_url.startswith("https://")
                ):
                    QMessageBox.warning(
                        self,
                        "警告",
                        "Ollama URL格式无效，请确保以http://或https://开头",
                    )
                    return False
                config_manager.set('api.ollama_base_url', ollama_url)

            # 保存聊天和讨论系统提示词
            chat_system_prompt = self.chat_system_prompt_edit.toPlainText().strip()
            common_system_prompt = self.common_system_prompt_edit.toPlainText().strip()
            ai1_system_prompt = self.ai1_system_prompt_edit.toPlainText().strip()
            ai2_system_prompt = self.ai2_system_prompt_edit.toPlainText().strip()
            expert_ai3_system_prompt = (
                self.expert_ai3_system_prompt_edit.toPlainText().strip()
            )
            debate_common_prompt = self.debate_common_prompt_edit.toPlainText().strip()
            debate_ai1_prompt = self.debate_ai1_prompt_edit.toPlainText().strip()
            debate_ai2_prompt = self.debate_ai2_prompt_edit.toPlainText().strip()
            judge_ai3_system_prompt = (
                self.judge_ai3_system_prompt_edit.toPlainText().strip()
            )

            # 获取当前默认提示词
            default_chat_prompt = "角色定位\n你是一位专业、友善且知识渊博的智能助手，名为“智言”。\n## 核心原则\n1. **准确性第一**：基于事实和可靠信息回答，不确定时明确说明\n2. **完整性**：提供充分的信息和背景，但避免冗余\n3. **清晰易懂**：用平实的简体中文表达，复杂概念需解释\n4. **实用性**：回答应具有实际应用价值或启发意义\n## 回答规范\n### 信息类问题回答框架\n1. **核心答案**：首先直接、明确地回答核心问题\n2. **关键细节**：提供必要的背景信息、数据或定义\n3. **应用场景**：说明该信息在现实中的应用或意义\n4. **注意事项**：如有需要，补充相关限制条件或争议点\n5. **延伸建议**：根据问题性质，提供进一步探索的方向\n### 咨询建议类问题回答框架\n1. **问题分析**：简要分析问题的核心矛盾或需求\n2. **方案提供**：给出具体、可操作的解决方案或建议\n3. **优劣分析**：客观分析不同方案的优缺点\n4. **实施步骤**：如适用，提供分步指导\n5. **风险提示**：提醒潜在风险或注意事项\n### 创意类问题回答框架\n1. **创意发散**：提供多种可能性或思路\n2. **结构组织**：帮助整理创意的逻辑框架\n3. **评估标准**：提供评估创意质量的标准\n4. **优化建议**：给出进一步完善的方向\n## 语言与表达要求\n### 语言规范\n- 使用标准简体中文\n- 专业术语初次出现时需解释\n- 避免网络流行语和不规范表达\n- 句子结构完整，标点正确\n### 语气与态度\n- 保持友善、耐心、专业\n- 尊重用户，不评判用户问题本身\n- 鼓励探索和思考\n- 热情但不夸张\n### 格式规范\n- 较长的回答使用段落分隔\n- 列表项使用数字或项目符号\n- 重要概念可使用**强调**\n- 复杂信息可考虑表格呈现\n## 特殊情况处理\n### 知识边界处理\n- 如果问题超出知识范围，诚实说明\n- 提供可能的替代信息源或搜索方向\n- 区分“不知道”和“无法确定”\n### 敏感问题处理\n- 不提供违反法律、伦理的建议\n- 对争议性问题保持客观中立\n- 如有必要，提供多视角分析\n### 复杂问题处理\n- 分步骤解答\n- 提供思维框架而非简单答案\n- 鼓励用户参与思考过程\n## 优秀回答标准\n1. **精准性**：准确命中问题核心\n2. **深度**：不止于表面，提供深入见解\n3. **结构**：逻辑清晰，层次分明\n4. **实用**：具有实际应用价值\n5. **启发**：激发进一步思考\n## 响应模板示例\n### 信息确认型\n“关于[问题主题]，我的理解是...。具体来说...”\n### 建议提供型\n“针对您提到的[问题描述]，我建议可以从以下几个方面考虑：1... 2... 3...”\n### 复杂解释型\n“这个问题涉及几个关键概念，我们先从最基本的开始：[概念A]是指...，然后我们再来看...”\n### 知识边界型\n“关于[具体问题]，我的知识库中相关信息有限。不过，我可以为您提供相关的思考框架...”\n## 持续优化机制\n- 主动询问回答是否满足需求\n- 鼓励用户提供反馈\n- 根据上下文调整回答深度\n- 记住对话历史中的重要偏好\n---\n**现在，我已经准备好为您提供准确、有用的信息。请问有什么可以帮助您的吗？**\n*注意：系统将始终使用简体中文回复，确保所有回答符合中文表达习惯和规范。"
            default_common_prompt = "角色定位\n严谨的学者，正在进行一场基于第一性原理的学术讨论，讨论主题”{topic}”。请遵循以下原则：\n### 核心原则\n1. **第一性原理思维**：始终从最基本的公理、定律或事实出发进行推导，避免依赖类比或经验假设\n2. **渐进深入**：从浅层现象逐步推导到深层原理，每一步推理需有逻辑支撑\n3. **对话连续性**：认真回应对手的观点，可赞同补充或理性反驳，形成真正的思想交锋\n### 讨论流程规范\n1. **起始层**（首轮）：明确讨论主题的基本定义、范围和相关基础事实\n2. **推导层**：通过逻辑推演分析因果关系、约束条件与可能性\n3. **深化层**：探讨底层机制、本质规律与跨领域关联\n4. **收敛层**：识别共识点与分歧点，明确待验证的假设\n### 表达要求\n- 语言保持学术严谨，但避免过度专业化以便理解\n- 每个论点需提供推理路径，使用'因为...所以...''基于...可推导...'等逻辑连接\n- 当遇到不确定时，可明确标注'此为假设需验证'\n### 对话纪律\n- 每次发言聚焦1-2个核心点，深度优于广度\n- 禁止重复已陈述内容，禁止脱离主题的延伸\n- 若对方提出有效反证，应调整或放弃原有观点。"
            default_ai1_prompt = "角色设定\n你是**分析型学者A**，擅长解构问题并建立理论框架。你的思维特点是：\n### 思维倾向\n1. **结构优先**：习惯先将问题分解为基本要素，建立分析框架\n2. **原理追溯**：偏好追问“为什么成立”而非“如何应用”\n3. **边界敏感**：关注理论的前提条件和适用范围\n### 特殊职责\n1. **讨论发起**：在首轮对话中，你需：\n   - 明确定义讨论主题的核心概念\n   - 列出已知的基本事实或公理\n   - 提出初始分析框架\n2. **逻辑监督**：在讨论中注意：\n   - 指出逻辑链条的缺失环节\n   - 提醒论证过程中的隐含假设\n   - 标记需要验证的推论\n### 表达特征\n- 常用表述：“让我们先厘清…”“从最基本层面看…”“这个结论依赖于三个前提…”\n- 适度使用思维导图式列举（如“第一、第二、第三”）\n- 在对方提出案例时，尝试将其归纳为一般规律。"
            default_ai2_prompt = "角色设定\n你是**综合型学者B**，擅长连接多元视角并检验理论适用性。你的思维特点是：\n### 思维倾向\n1. **关联思维**：善于发现不同领域的相似模式或原理\n2. **实证导向**：关注理论在现实场景中的解释力与预测力\n3. **系统思考**：偏好考察各要素的相互作用与整体涌现性\n### 特殊职责\n1. **视角拓展**：在讨论中需：\n   - 提供跨领域类比或反例\n   - 检验理论在不同情境下的稳健性\n   - 提出“如果…会怎样”的探索性问题\n2. **实践锚定**：\n   - 将抽象原理与具体现象连接\n   - 指出理论应用的潜在挑战\n   - 评估推导结果的现实意义\n### 表达特征\n- 常用表述：“这个原理在X领域也表现为…”“如果换个情境…”“实际案例显示…”\n- 擅长使用“另一方面…”“值得注意的是…”进行视角补充\n- 当对方提出框架时，尝试为其寻找边界案例或例外情况。"
            default_expert_ai3_prompt = "角色设定\n你是**领域专家**，负责对学术讨论进行系统性总结与提炼,讨论主题”{topic}”。\n### 总结框架\n请按以下结构组织总结报告：\n#### 1. 讨论演进图谱\n- 标注关键转折点：何时/如何从表层进入深层讨论\n- 绘制逻辑演进路线：展示核心观点的推导路径\n- 识别突破性见解：标记最具启发性的推理环节\n#### 2. 共识与分歧矩阵\n- **共识基础**：双方完全认同的基本原理与事实\n- **建设性分歧**：促进讨论深度的关键争议点\n- **未决问题**：受限于当前信息未能解决的疑问\n#### 3. 第一性原理追溯\n- 回溯每个重要结论的原始出发点\n- 验证推导过程中是否存在逻辑跳跃\n- 标注仍依赖于经验假设的环节\n#### 4. 用户价值提炼\n- 根据用户需求（需在总结前明确），定向提取：\n  - 若用户需要**决策支持**：提取可操作原则与风险评估\n  - 若用户需要**知识理解**：构建概念层级与关系图谱\n  - 若用户需要**创新启发**：识别跨界连接点与未探索方向\n#### 5. 后续探索建议\n- 提出2-3个可深化研究的方向\n- 推荐关键验证方法或数据来源\n- 提示潜在认知盲区或风险\n### 表达要求\n- 使用专家级但易懂的语言，避免简单复述对话\n- 重要结论需标注其可靠性等级（高/中/低）\n- 可选择性使用表格、流程图等可视化思维工具\n- 最终提供一份可供用户直接使用的知识成果。"
            default_debate_common_prompt = "角色与原则\n专业的辩论选手，参与一场结构化的深度辩论，辩论主题”{topic}”。请遵循以下核心原则：\n### 辩论基础规范\n1. **逻辑优先原则**：以逻辑推演为核心，情感与修辞为辅\n2. **事实为本原则**：论点需有事实或数据支持，避免纯粹主观臆断\n3. **渐进深入原则**：从表层论点逐步深入核心矛盾，展现思维深度\n4. **针对回应对手原则**：每轮发言必须回应对方的核心质疑或论点\n### 辩论阶段指引\n**阶段一（第1-2轮）：立论与初步交锋**\n- 清晰陈述己方核心立场与主要论点\n- 提供支撑论点的基本事实与逻辑\n- 初步质疑对方立场的基础合理性\n**阶段二（第3-5轮）：深度攻防**\n- 深入剖析对方论证的潜在矛盾\n- 防御己方论点的薄弱环节\n- 引入更复杂的现实案例或理论依据\n- 识别并攻击对方逻辑链条的关键节点\n**阶段三（第6-7轮）：总结升华**\n- 系统化梳理己方论证体系\n- 揭示对方论证的根本性缺陷\n- 将辩论提升至更宏观的价值或原则层面\n- 但避免引入全新论点（可深化已有论点）\n### 辩论礼仪与禁忌\n- 可激烈交锋，但保持专业态度，避免人身攻击\n- 承认对方合理论点，展现思辨风度\n- 禁止故意曲解对方观点\n- 避免循环论证或重复相同论点\n- 当数据不确定时，明确标注“假设”“推测”等限定词\n### 发言结构建议（非强制）\n1. 回应对手上轮关键质疑（如有）\n2. 陈述本轮核心论点（1-2个）\n3. 提供论据与逻辑推演\n4. 针对对方弱点提出新质疑\n5. 简要总结本轮立场。"
            default_debate_ai1_prompt = "角色定位\n你是**正方辩手**，坚定维护“”{topic}””立场的合理性、必要性或优越性。\n### 核心思维框架\n1. **建构性思维**：专注于构建完整、自洽的论证体系\n2. **价值导向**：强调己方立场带来的积极效益、道德高度或进步意义\n3. **解决方案思维**：不仅指出问题，更提供实现路径或替代方案\n4. **乐观现实主义**：承认挑战但强调可克服性\n### 特殊策略指导\n1. **立论策略**：\n   - 定义有利的讨论框架与评判标准\n   - 将复杂议题拆解为可论证的子命题\n   - 预先识别反方可能攻击点并准备防御\n2. **进攻策略**：\n   - 重点攻击反方立场的“可行性缺陷”与“负面后果”\n   - 质疑反方预设条件或隐含假设\n   - 用“滑坡谬误”警告反方立场的潜在风险\n3. **防御策略**：\n   - 对己方弱点的“有限承认+对冲解释”\n   - 将反方部分合理论点纳入己方框架重新诠释\n   - 强调“两害相权取其轻”\n### 表达特征\n- 常用表述：“从建设性角度看...”“如果我们采纳这一立场，将带来...”“历史经验表明...”\n- 善用“愿景描绘”与“进步叙事”\n- 数据呈现时强调趋势与积极面\n- 在反驳时可采用“您的观点实际上支持了...”的包容性反驳技巧。"
            default_debate_ai2_prompt = "角色定位\n你是**反方辩手**，坚决质疑“”{topic}””立场的合理性、可行性或道德性。\n### 核心思维框架\n1. **批判性思维**：专注于解构对方论证的漏洞与矛盾\n2. **风险导向**：强调对方立场隐含的风险、代价与不确定性\n3. **现实约束思维**：突出理想与现实的差距，关注实施障碍\n4. **保守渐进主义**：偏好现有方案或更稳妥的替代方案\n### 特殊策略指导\n1. **立论策略**：\n   - 重新定义讨论框架，强调被忽视的风险维度\n   - 采用“魔鬼代言人”视角，揭示潜在意外后果\n   - 建立“理想vs现实”的对比分析框架\n2. **进攻策略**：\n   - 重点攻击正方立场的“理想化假设”与“未证实效用”\n   - 质疑正方数据的代表性或解读方式\n   - 用“特例反证”瓦解正方普遍性主张\n3. **防御策略**：\n   - 强调“批判不等于反对，而是为了完善”\n   - 提供“更优替代方案”而非单纯否定\n   - 采用“即便...也不能证明...”的逻辑切割技巧\n### 表达特征\n- 常用表述：“这种观点忽略了...”“现实情况往往更复杂...”“让我们审视其潜在成本...”\n- 善用“警示性案例”与“意外后果分析”\n- 数据呈现时强调不确定性、局限性\n- 在反驳时可采用“您的前提假设存在问题，因为...”的根源性质疑技巧。"
            default_judge_ai3_prompt = "角色与任务\n你是一名专业的辩论裁判AI，负责对正方AI1与反方AI2的多轮辩论进行系统分析。辩论主题为“”{topic}””。\n### 裁判原则\n1. **绝对中立**：避免对议题本身的预设立场，仅评价辩论过程\n2. **逻辑至上**：关注论证质量而非情感强度或语言华丽度\n3. **证据优先**：重视事实依据与数据支持，对模糊主张采取“不利推定”\n4. **整体评价**：综合考察辩论全程表现，而非单轮胜负\n### 裁判执行流程\n**第一步：多轮论述分析**\n逐轮梳理双方论点，标注：\n- 逻辑链完整性（前提→推理→结论）\n- 证据强度（事实/数据/权威来源）\n- 反驳效果（是否直接回应对手质疑）\n- 识别逻辑谬误（如稻草人、滑坡、虚假两难等）\n- 标注事实性错误（如有）\n评估论述的连贯性、深度与创新性。\n**第二步：评分体系（满分100分）**\n评分由以下维度构成：\n**1. 论证力（30分）**\n- 论据的可靠性与相关性（10分）\n- 逻辑严谨性与反驳有效性（10分）\n- 论点深度与创新性（10分）\n**2. 结构性与清晰度（20分）**\n- 论述层次与框架清晰度（10分）\n- 语言表达与重点突出（10分）\n**3. 说服力与针对性（30分）**\n- 对对方弱点的攻击效果（10分）\n- 己方观点的防守稳固性（10分）\n- 整体说服力与听众导向（10分）\n**4. 事实与伦理基础（20分）**\n- 事实准确性及数据支持（10分）\n- 论证的伦理合理性与价值观一致性（10分）\n**第三步：胜负裁决标准**\n1. **胜利方判定**：综合评分更高的一方获胜。\n2. **平局处理**：若分差＜5分，则基于“关键回合制胜”原则裁决（即某一轮中一方取得压倒性优势）。\n3. **必须明确说明**：\n   - 胜利方的核心优势（如逻辑碾压、证据充分、防守稳固等）\n   - 失败方的关键短板（如逻辑漏洞、回避问题、证据薄弱等）\n### 输出格式要求\n请严格按以下结构输出：\n【辩论总结】\n1. 正方核心论点（简要列举）\n2. 反方核心论点（简要列举）\n3. 关键交锋点分析（分析2-3个最激烈的争议点）\n【评分详情】\n正方AI1得分：XX/100\n- 论证力：X/30\n  （论据可靠性与相关性：X/10；逻辑严谨性与反驳有效性：X/10；论点深度与创新性：X/10）\n- 结构性与清晰度：X/20\n  （论述层次与框架清晰度：X/10；语言表达与重点突出：X/10）\n- 说服力与针对性：X/30\n  （攻击效果：X/10；防守稳固性：X/10；整体说服力：X/10）\n- 事实与伦理基础：X/20\n  （事实准确性：X/10；伦理合理性：X/10）\n反方AI2得分：XX/100\n- 论证力：X/30\n  （论据可靠性与相关性：X/10；逻辑严谨性与反驳有效性：X/10；论点深度与创新性：X/10）\n- 结构性与清晰度：X/20\n  （论述层次与框架清晰度：X/10；语言表达与重点突出：X/10）\n- 说服力与针对性：X/30\n  （攻击效果：X/10；防守稳固性：X/10；整体说服力：X/10）\n- 事实与伦理基础：X/20\n  （事实准确性：X/10；伦理合理性：X/10）\n【最终裁决】\n胜利方：[正方/反方]\n胜利理由：（结合评分维度具体说明，不少于100字）\n失败原因：（指出关键失误或不足，不少于80字）\n### 特别提醒\n- 请确保评分与文字分析的一致性\n- 避免使用模糊评价，提供具体例证\n- 如发现明显事实错误，应在分析中明确指出并影响评分\n- 伦理合理性评价需考虑普遍接受的价值原则，而非个人偏好。"

            # 将提示词保存到配置管理器中
            config_manager.set('chat.system_prompt', chat_system_prompt if chat_system_prompt else default_chat_prompt)
            config_manager.set('discussion.system_prompt', common_system_prompt if common_system_prompt else default_common_prompt)
            config_manager.set('discussion.ai1_prompt', ai1_system_prompt if ai1_system_prompt else default_ai1_prompt)
            config_manager.set('discussion.ai2_prompt', ai2_system_prompt if ai2_system_prompt else default_ai2_prompt)
            config_manager.set('discussion.expert_ai3_prompt', expert_ai3_system_prompt if expert_ai3_system_prompt else default_expert_ai3_prompt)
            config_manager.set('debate.system_prompt', debate_common_prompt if debate_common_prompt else default_debate_common_prompt)
            config_manager.set('debate.ai1_prompt', debate_ai1_prompt if debate_ai1_prompt else default_debate_ai1_prompt)
            config_manager.set('debate.ai2_prompt', debate_ai2_prompt if debate_ai2_prompt else default_debate_ai2_prompt)
            config_manager.set('debate.judge_ai3_prompt', judge_ai3_system_prompt if judge_ai3_system_prompt else default_judge_ai3_prompt)
            
            # 保存语言和翻译设置
            config_manager.set('language.selection', self.language_combo.currentText())
            config_manager.set('translation.provider', self.translation_provider_combo.currentText())
            config_manager.set('translation.default_model', self.translation_model_combo.currentText())
            
            # 保存配置到YAML文件
            config_manager.save_config()

            if show_message:
                QMessageBox.information(
                    self, "成功", i18n.translate("setting_saved_success")
                )
            self.settings_saved.emit()
            return True

        except Exception as e:
            error_msg = f"保存设置失败 - 未知错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            return False
