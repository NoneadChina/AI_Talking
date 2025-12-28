# -*- coding: utf-8 -*-
"""
API设置窗口部件，用于配置各种AI API的连接信息和系统提示词。

该部件提供了一个界面，允许用户配置OpenAI、DeepSeek和Ollama的API设置，
以及各种系统提示词。
"""

import sys
import os
from dotenv import load_dotenv
from utils.logger_config import get_logger
from utils.i18n_manager import i18n
from utils.secure_storage import encrypt_data, decrypt_data
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
        self.translation_provider_combo.addItems(["OpenAI", "DeepSeek", "Ollama"])
        self.translation_provider_combo.setStyleSheet(
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
        provider_layout.addWidget(self.translation_provider_combo)
        provider_layout.addStretch()
        translation_layout.addLayout(provider_layout)

        # 翻译默认模型
        model_layout = QHBoxLayout()
        model_layout.setSpacing(10)
        self.default_model_label = QLabel(i18n.translate("setting_default_model"))
        model_layout.addWidget(self.default_model_label, alignment=Qt.AlignVCenter)
        self.translation_model_combo = QComboBox()
        self.translation_model_combo.addItems(
            ["gpt-4o", "gpt-3.5-turbo", "deepseek-chat", "llama3"]
        )
        self.translation_model_combo.setStyleSheet(
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

        从环境变量中读取之前保存的配置信息并填充到表单中，包括：
        1. API密钥
        2. Ollama URL
        3. 系统提示词
        """
        # 加载API密钥和URL - 解密密钥
        from utils.secure_storage import decrypt_data
        self.openai_key_edit.setText(decrypt_data(os.getenv("OPENAI_API_KEY", "")))
        self.deepseek_key_edit.setText(decrypt_data(os.getenv("DEEPSEEK_API_KEY", "")))
        self.ollama_cloud_key_edit.setText(decrypt_data(os.getenv("OLLAMA_CLOUD_API_KEY", "")))
        self.ollama_cloud_url_edit.setText(
            os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com")
        )
        self.ollama_url_edit.setText(
            os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )

        # 加载系统提示词
        # 聊天系统提示词
        default_chat_prompt = "请使用简体中文回答"
        self.chat_system_prompt_edit.setPlainText(
            os.getenv("CHAT_SYSTEM_PROMPT", default_chat_prompt)
        )

        # 讨论共享系统提示词
        default_common_prompt = "你是一个参与讨论的AI助手。请根据收到的内容深入思考，并回应，多次回答时尽量从不同角度深入分析。使用第一性原理进行讨论，是一场高强度的智力合作与交锋。这不仅仅是普通的辩论或交流，而是试图共同逼近问题最根本的真相。"
        self.common_system_prompt_edit.setPlainText(
            os.getenv("DISCUSSION_SYSTEM_PROMPT", default_common_prompt)
        )

        # 讨论AI1系统提示词
        default_ai1_prompt = '思维层面-第一性原理的"引擎"，解构与还原能力，概念清晰化与定义能力，公理化思维与逻辑推理能力，批判性思维与溯因能力，系统思维与重建能力'
        self.ai1_system_prompt_edit.setPlainText(
            os.getenv("DISCUSSION_AI1_SYSTEM_PROMPT", default_ai1_prompt)
        )

        # 讨论AI2系统提示词
        default_ai2_prompt = '沟通与协作层面：第一性原理的"桥梁"，苏格拉底式提问术，主动倾听与精准复述，元沟通能力'
        self.ai2_system_prompt_edit.setPlainText(
            os.getenv("DISCUSSION_AI2_SYSTEM_PROMPT", default_ai2_prompt)
        )

        # 专家AI3系统提示词
        default_expert_ai3_prompt = "你是一位学术讨论分析师，负责对讨论进行总结和分析。请根据讨论内容提供深入的总结、核心论点梳理和讨论质量评估。"
        self.expert_ai3_system_prompt_edit.setPlainText(
            os.getenv("EXPERT_AI3_SYSTEM_PROMPT", default_expert_ai3_prompt)
        )

        # 加载辩论系统提示词
        # 辩论共享系统提示词
        default_debate_common_prompt = '你是一个辩论选手，请根据你的立场进行辩论，逻辑清晰，论点明确。能够梳理复杂问题，构建严密的论证链条，并能识别他人逻辑中的漏洞，快速搜集、筛选、消化和整合大量资料、数据、案例与理论，并将其转化为有力的论据。能够用清晰、简洁、有感染力的语言陈述观点，避免歧义。包括书面陈词和即兴口语。不仅要听对方"说了什么"，更要听出"没说什么"以及"逻辑断层在哪里"，并迅速组织语言进行回应。'
        self.debate_common_prompt_edit.setPlainText(
            os.getenv("DEBATE_SYSTEM_PROMPT", default_debate_common_prompt)
        )

        # 正方辩手AI1系统提示词
        default_debate_ai1_prompt = '你是正方辩手，构建一个完整、稳固、有吸引力的体系（己方立场）。建立并捍卫一个完整的论证体系。 "为什么这个观点是成立的？" 需要主动提供理由。给出一个有利于本方论证且公允、有说服力的定义，作为大厦的基石。论点之间要相互支撑，形成闭环。讲一个"好故事"。设立一个评判胜负的尺度（如"何者更有利于公平"），并证明己方完全符合。通过描绘美好愿景（采纳我方立场后的积极世界）来引发共鸣。归纳法（用多个例子证明规律）、演绎法（用公认原理推导个案）、价值升华。第一次回答不做回应反方质疑。'
        self.debate_ai1_prompt_edit.setPlainText(
            os.getenv("DEBATE_AI1_SYSTEM_PROMPT", default_debate_ai1_prompt)
        )

        # 反方辩手AI2系统提示词
        default_debate_ai2_prompt = '你是反方辩手，找出对方体系的裂缝并将其攻破，同时有机会也会树立自己的替代方案。质疑、挑战并试图瓦解正方的体系。证伪思维： "这个观点在什么地方不成立？" 需要主动寻找漏洞。指出正方定义的狭隘、不公或偏颇，并提出一个更合理或利于己方的替代定义。攻击对方最薄弱、最核心的环节（"擒贼先擒王"）。不必追求体系完整，但求攻击有效。质疑正方标准的合理性，或提出一个新的、更优的标准，并在新标准下证明己方优势。通过揭示风险、弊端（采纳正方立场后的消极后果）来引发警惕。归谬法（引申出荒谬结论）、举反例（一个反例足以动摇普遍结论）、数据质疑、切割论证（指出对方混淆了不同概念）。'
        self.debate_ai2_prompt_edit.setPlainText(
            os.getenv("DEBATE_AI2_SYSTEM_PROMPT", default_debate_ai2_prompt)
        )

        # 裁判AI3系统提示词
        default_judge_ai3_prompt = "你是一个辩论裁判，负责对辩论进行评分和总结。辩论主题是：{topic}。请根据辩论内容给出公正的评分和总结。"
        self.judge_ai3_system_prompt_edit.setPlainText(
            os.getenv("JUDGE_AI3_SYSTEM_PROMPT", default_judge_ai3_prompt)
        )

        # 加载语言选择设置
        self.language_combo.setCurrentText(os.getenv("LANGUAGE_SELECTION", "简体中文"))

        # 加载翻译设置
        self.translation_provider_combo.setCurrentText(
            os.getenv("TRANSLATION_PROVIDER", "openai")
        )
        self.translation_model_combo.setCurrentText(
            os.getenv("TRANSLATION_DEFAULT_MODEL", "gpt-4o")
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

    def save_settings(self, show_message=True, show_confirm=True):
        """
        保存API设置到.env文件。

        将用户在界面上配置的API密钥、Ollama URL和系统提示词保存到环境配置文件中。
        保存前会备份原文件，确保数据安全。

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
            # 确定应用程序的安装目录，与main.py保持一致
            import sys

            if getattr(sys, "frozen", False):
                # 打包后的可执行文件所在目录
                current_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境下的当前文件所在目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                current_dir = os.path.dirname(current_dir)  # 向上一级目录
                current_dir = os.path.dirname(current_dir)  # 再向上一级目录

            # 使用应用程序安装目录作为.env文件的保存位置
            env_path = os.path.join(current_dir, ".env")
            env_content = []

            # 如果文件已存在，读取现有内容
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        env_content = f.readlines()
                except IOError as e:
                    QMessageBox.critical(self, "错误", f"读取.env文件失败: {str(e)}")
                    return False

            # 解析现有配置到字典
            config = {}
            for line in env_content:
                line = line.rstrip("\n")
                if "=" in line and not line.strip().startswith("#"):  # 忽略注释行
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

            # 更新OpenAI API密钥配置 - 始终更新，无论是否为空
            openai_key = self.openai_key_edit.text().strip()
            if openai_key:
                config["OPENAI_API_KEY"] = encrypt_data(openai_key)
            elif "OPENAI_API_KEY" in config:
                del config["OPENAI_API_KEY"]  # 如果用户删除了密钥，从配置中移除

            # 更新DeepSeek API密钥配置 - 始终更新，无论是否为空
            deepseek_key = self.deepseek_key_edit.text().strip()
            if deepseek_key:
                config["DEEPSEEK_API_KEY"] = encrypt_data(deepseek_key)
            elif "DEEPSEEK_API_KEY" in config:
                del config["DEEPSEEK_API_KEY"]  # 如果用户删除了密钥，从配置中移除

            # 更新Ollama Cloud API密钥配置 - 始终更新，无论是否为空
            ollama_cloud_key = self.ollama_cloud_key_edit.text().strip()
            ollama_cloud_url = self.ollama_cloud_url_edit.text().strip()
            if ollama_cloud_key:
                config["OLLAMA_CLOUD_API_KEY"] = encrypt_data(ollama_cloud_key)
                if ollama_cloud_url:
                    # 保存用户设置的Ollama Cloud地址
                    config["OLLAMA_CLOUD_BASE_URL"] = ollama_cloud_url
                else:
                    # 使用默认地址
                    config["OLLAMA_CLOUD_BASE_URL"] = "https://ollama.com"
            elif "OLLAMA_CLOUD_API_KEY" in config:
                del config["OLLAMA_CLOUD_API_KEY"]  # 如果用户删除了密钥，从配置中移除
                if "OLLAMA_CLOUD_BASE_URL" in config:
                    del config["OLLAMA_CLOUD_BASE_URL"]

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

                # 保存URL，无论是否为默认值
                config["OLLAMA_BASE_URL"] = ollama_url
            elif "OLLAMA_BASE_URL" in config:
                del config["OLLAMA_BASE_URL"]  # 如果URL为空，删除现有配置

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
            default_chat_prompt = "请使用简体中文回答"
            default_common_prompt = "你是一个参与讨论的AI助手。请根据收到的内容深入思考，并回应，多次回答时尽量从不同角度深入分析。使用第一性原理进行讨论，是一场高强度的智力合作与交锋。这不仅仅是普通的辩论或交流，而是试图共同逼近问题最根本的真相。"
            default_ai1_prompt = '思维层面-第一性原理的"引擎"，解构与还原能力，概念清晰化与定义能力，公理化思维与逻辑推理能力，批判性思维与溯因能力，系统思维与重建能力'
            default_ai2_prompt = '沟通与协作层面：第一性原理的"桥梁"，苏格拉底式提问术，主动倾听与精准复述，元沟通能力'
            default_expert_ai3_prompt = "你是一位学术讨论分析师，负责对讨论进行总结和分析。请根据讨论内容提供深入的总结、核心论点梳理和讨论质量评估。"
            default_debate_common_prompt = '你是一个辩论选手，请根据你的立场进行辩论，逻辑清晰，论点明确。能够梳理复杂问题，构建严密的论证链条，并能识别他人逻辑中的漏洞，快速搜集、筛选、消化和整合大量资料、数据、案例与理论，并将其转化为有力的论据。能够用清晰、简洁、有感染力的语言陈述观点，避免歧义。包括书面陈词和即兴口语。不仅要听对方"说了什么"，更要听出"没说什么"以及"逻辑断层在哪里"，并迅速组织语言进行回应。'
            default_debate_ai1_prompt = '你是正方辩手，构建一个完整、稳固、有吸引力的体系（己方立场）。建立并捍卫一个完整的论证体系。 "为什么这个观点是成立的？" 需要主动提供理由。给出一个有利于本方论证且公允、有说服力的定义，作为大厦的基石。论点之间要相互支撑，形成闭环。讲一个"好故事"。设立一个评判胜负的尺度（如"何者更有利于公平"），并证明己方完全符合。通过描绘美好愿景（采纳我方立场后的积极世界）来引发共鸣。归纳法（用多个例子证明规律）、演绎法（用公认原理推导个案）、价值升华。第一次回答不做回应反方质疑。'
            default_debate_ai2_prompt = '你是反方辩手，找出对方体系的裂缝并将其攻破，同时有机会也会树立自己的替代方案。质疑、挑战并试图瓦解正方的体系。证伪思维： "这个观点在什么地方不成立？" 需要主动寻找漏洞。指出正方定义的狭隘、不公或偏颇，并提出一个更合理或利于己方的替代定义。攻击对方最薄弱、最核心的环节（"擒贼先擒王"）。不必追求体系完整，但求攻击有效。质疑正方标准的合理性，或提出一个新的、更优的标准，并在新标准下证明己方优势。通过揭示风险、弊端（采纳正方立场后的消极后果）来引发警惕。归谬法（引申出荒谬结论）、举反例（一个反例足以动摇普遍结论）、数据质疑、切割论证（指出对方混淆了不同概念）。'
            default_judge_ai3_prompt = "你是一个辩论裁判，负责对辩论进行评分和总结。辩论主题是：{topic}。请根据辩论内容给出公正的评分和总结。"

            # 保存所有提示词，无论是否为默认值
            config["CHAT_SYSTEM_PROMPT"] = (
                chat_system_prompt if chat_system_prompt else default_chat_prompt
            )
            config["DISCUSSION_SYSTEM_PROMPT"] = (
                common_system_prompt if common_system_prompt else default_common_prompt
            )
            config["DISCUSSION_AI1_SYSTEM_PROMPT"] = (
                ai1_system_prompt if ai1_system_prompt else default_ai1_prompt
            )
            config["DISCUSSION_AI2_SYSTEM_PROMPT"] = (
                ai2_system_prompt if ai2_system_prompt else default_ai2_prompt
            )
            config["DEBATE_SYSTEM_PROMPT"] = (
                debate_common_prompt
                if debate_common_prompt
                else default_debate_common_prompt
            )
            config["DEBATE_AI1_SYSTEM_PROMPT"] = (
                debate_ai1_prompt if debate_ai1_prompt else default_debate_ai1_prompt
            )
            config["DEBATE_AI2_SYSTEM_PROMPT"] = (
                debate_ai2_prompt if debate_ai2_prompt else default_debate_ai2_prompt
            )
            config["EXPERT_AI3_SYSTEM_PROMPT"] = (
                expert_ai3_system_prompt
                if expert_ai3_system_prompt
                else default_expert_ai3_prompt
            )
            config["JUDGE_AI3_SYSTEM_PROMPT"] = (
                judge_ai3_system_prompt
                if judge_ai3_system_prompt
                else default_judge_ai3_prompt
            )

            # 保存新添加的设置
            config["LANGUAGE_SELECTION"] = self.language_combo.currentText()
            config["TRANSLATION_PROVIDER"] = (
                self.translation_provider_combo.currentText()
            )
            config["TRANSLATION_DEFAULT_MODEL"] = (
                self.translation_model_combo.currentText()
            )

            # 移除旧的键名（兼容性处理）
            old_keys = [
                "COMMON_SYSTEM_PROMPT",
                "AI1_SYSTEM_PROMPT",
                "AI2_SYSTEM_PROMPT",
                "DEBATE_COMMON_PROMPT",
                "DEBATE_AI1_PROMPT",
                "DEBATE_AI2_PROMPT",
            ]
            for key in old_keys:
                if key in config:
                    del config[key]

            # 写回.env文件 - 先备份原文件（安全措施）
            backup_path = None
            if os.path.exists(env_path):
                backup_path = env_path + ".backup"
                try:
                    import shutil

                    shutil.copy2(env_path, backup_path)
                    logger.info(f"配置文件备份成功: {env_path} -> {backup_path}")
                except Exception as e:
                    error_msg = f"无法备份配置文件: {str(e)}"
                    logger.error(error_msg)
                    QMessageBox.warning(self, "警告", error_msg)
                    # 继续执行，不因为备份失败而中断

            try:
                # 写入新的配置文件内容
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write("# API密钥配置\n\n")

                    # 写入OpenAI API配置
                    f.write(
                        f"# OpenAI API配置\nOPENAI_API_KEY={config.get('OPENAI_API_KEY', '')}\n\n"
                    )

                    # 写入DeepSeek API配置
                    f.write(
                        f"# DeepSeek API配置\nDEEPSEEK_API_KEY={config.get('DEEPSEEK_API_KEY', '')}\n\n"
                    )

                    # 写入Ollama Cloud API配置
                    f.write(
                        f"# Ollama Cloud API配置\nOLLAMA_CLOUD_API_KEY={config.get('OLLAMA_CLOUD_API_KEY', '')}\n"
                    )
                    f.write(
                        f"OLLAMA_CLOUD_BASE_URL={config.get('OLLAMA_CLOUD_BASE_URL', 'https://ollama.com')}\n\n"
                    )

                    # 写入Ollama API配置（总是写入，无论是否为默认值）
                    ollama_url = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
                    f.write(f"# Ollama API配置\nOLLAMA_BASE_URL={ollama_url}\n\n")

                    # 写入基本设置
                    f.write("# 基本设置\n")
                    f.write(
                        f"LANGUAGE_SELECTION={config.get('LANGUAGE_SELECTION', '简体中文')}\n"
                    )
                    f.write(
                        f"TRANSLATION_PROVIDER={config.get('TRANSLATION_PROVIDER', 'openai')}\n"
                    )
                    f.write(
                        f"TRANSLATION_DEFAULT_MODEL={config.get('TRANSLATION_DEFAULT_MODEL', 'gpt-4o')}\n\n"
                    )

                    # 写入系统提示词配置
                    f.write("# 系统提示词配置\n")

                    # 写入所有系统提示词，无论是否为默认值
                    # 聊天系统提示词
                    if "CHAT_SYSTEM_PROMPT" in config:
                        prompt = config["CHAT_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"CHAT_SYSTEM_PROMPT={prompt}\n")

                    # 讨论系统提示词
                    if "DISCUSSION_SYSTEM_PROMPT" in config:
                        prompt = config["DISCUSSION_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"DISCUSSION_SYSTEM_PROMPT={prompt}\n")

                    if "DISCUSSION_AI1_SYSTEM_PROMPT" in config:
                        prompt = config["DISCUSSION_AI1_SYSTEM_PROMPT"].replace(
                            "\n", "\\n"
                        )
                        f.write(f"DISCUSSION_AI1_SYSTEM_PROMPT={prompt}\n")

                    if "DISCUSSION_AI2_SYSTEM_PROMPT" in config:
                        prompt = config["DISCUSSION_AI2_SYSTEM_PROMPT"].replace(
                            "\n", "\\n"
                        )
                        f.write(f"DISCUSSION_AI2_SYSTEM_PROMPT={prompt}\n")

                    # 专家AI3系统提示词
                    if "EXPERT_AI3_SYSTEM_PROMPT" in config:
                        prompt = config["EXPERT_AI3_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"EXPERT_AI3_SYSTEM_PROMPT={prompt}\n")

                    # 辩论系统提示词
                    if "DEBATE_SYSTEM_PROMPT" in config:
                        prompt = config["DEBATE_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"DEBATE_SYSTEM_PROMPT={prompt}\n")

                    if "DEBATE_AI1_SYSTEM_PROMPT" in config:
                        prompt = config["DEBATE_AI1_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"DEBATE_AI1_SYSTEM_PROMPT={prompt}\n")

                    if "DEBATE_AI2_SYSTEM_PROMPT" in config:
                        prompt = config["DEBATE_AI2_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"DEBATE_AI2_SYSTEM_PROMPT={prompt}\n")

                    # 裁判AI3系统提示词
                    if "JUDGE_AI3_SYSTEM_PROMPT" in config:
                        prompt = config["JUDGE_AI3_SYSTEM_PROMPT"].replace("\n", "\\n")
                        f.write(f"JUDGE_AI3_SYSTEM_PROMPT={prompt}\n")
            except IOError as e:
                # 恢复备份文件
                if backup_path and os.path.exists(backup_path):
                    try:
                        import shutil

                        shutil.copy2(backup_path, env_path)
                        QMessageBox.warning(
                            self, "警告", f"保存配置失败，但已恢复备份: {str(e)}"
                        )
                    except Exception:
                        QMessageBox.critical(
                            self, "错误", f"保存配置失败且无法恢复备份: {str(e)}"
                        )
                else:
                    QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
                return False

            # 重新加载环境变量，确保所有模块都能获取到最新的设置
            load_dotenv(override=True)

            if show_message:
                QMessageBox.information(
                    self, "成功", i18n.translate("setting_saved_success")
                )
            self.settings_saved.emit()

        except IOError as e:
            error_msg = f"保存设置失败 - 文件IO错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            error_msg = f"保存设置失败 - 未知错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
