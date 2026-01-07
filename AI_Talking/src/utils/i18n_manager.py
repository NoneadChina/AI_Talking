# -*- coding: utf-8 -*-
"""
国际化管理模块，用于处理应用程序的多语言支持

该模块实现了应用程序的国际化功能，支持多种语言切换，
通过加载JSON格式的翻译文件，为应用程序提供统一的翻译接口。
"""

import os
import json
import logging
from typing import Dict, Optional
from PyQt5.QtCore import QLocale, QObject, pyqtSignal


class I18nManager(QObject):
    """
    国际化管理器，负责处理应用程序的多语言支持
    
    该类负责加载翻译文件、管理当前语言、提供翻译功能，
    并在语言变化时发送信号通知UI组件更新。
    """

    # 语言变化信号，当语言切换时发射此信号
    language_changed = pyqtSignal()

    def __init__(self):
        """
        初始化国际化管理器
        
        主要完成以下工作：
        1. 定义支持的语言列表
        2. 确定翻译资源目录路径
        3. 加载所有语言的翻译文件
        4. 设置当前语言为系统语言
        """
        super().__init__()

        # 支持的语言列表，键为语言代码，值为语言显示名称
        self.supported_languages = {
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "de": "Deutsch",
            "es": "Español",
            "fr": "Français",
            "ar": "العربية",
            "ru": "Русский",
        }

        # 翻译资源目录 - 处理PyInstaller打包后的路径差异
        import sys
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用PyInstaller提供的临时目录
            self.translations_dir = os.path.join(sys._MEIPASS, "src", "i8n")
        else:
            # 开发环境，使用相对路径计算
            self.translations_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "i8n"
            )

        # 翻译资源字典，存储所有语言的翻译数据
        # 结构: {语言代码: {翻译键: 翻译值}}
        self.translations: Dict[str, Dict[str, str]] = {}

        # 加载所有语言的翻译文件
        self._load_translations()

        # 当前语言，默认使用系统语言
        self.current_language = self.get_system_language()

    def _load_translations(self):
        """
        从JSON文件加载所有语言的翻译数据
        
        遍历所有支持的语言，加载对应的JSON翻译文件，
        处理可能出现的异常情况，确保程序稳定性。
        """
        for lang_code in self.supported_languages:
            try:
                # 构建翻译文件路径
                file_path = os.path.join(self.translations_dir, f"{lang_code}.json")
                # 读取并解析JSON翻译文件
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
                logging.info(f"Loaded translations for language: {lang_code}")
            except FileNotFoundError:
                # 翻译文件不存在时的处理
                logging.error(f"Translation file not found for language: {lang_code}")
                self.translations[lang_code] = {}  # 使用空字典作为默认值
            except json.JSONDecodeError as e:
                # JSON解析错误时的处理
                logging.error(
                    f"Error parsing translation file for language {lang_code}: {e}"
                )
                self.translations[lang_code] = {}  # 使用空字典作为默认值
            except Exception as e:
                # 其他意外错误时的处理
                logging.error(
                    f"Unexpected error loading translations for language {lang_code}: {e}"
                )
                self.translations[lang_code] = {}  # 使用空字典作为默认值

    def get_system_language(self) -> str:
        """
        获取操作系统语言
        
        根据系统语言返回相应的语言代码，
        对中文特殊处理，区分简体和繁体，
        其他语言只保留主语言代码。

        Returns:
            str: 语言代码，如 'zh-CN', 'en', 'ja' 等
        """
        # 获取系统当前语言
        locale = QLocale.system().name()
        # 将下划线替换为连字符，统一语言代码格式（如 'zh_CN' -> 'zh-CN'）
        locale = locale.replace("_", "-")
        
        # 特殊处理中文，保留简体和繁体的区分
        if locale.startswith("zh"):
            return locale  # 保留 'zh-CN' 或 'zh-TW'
        else:
            # 其他语言只保留主语言代码（如 'en-US' -> 'en'）
            return locale.split("-")[0]

    def set_language(self, language: str):
        """
        设置当前语言
        
        切换应用程序的当前语言，并在语言变化时发送信号通知UI更新。
        如果指定的语言不支持，则使用系统语言作为备选。

        Args:
            language: 语言代码，如 'zh-CN', 'en', 'ja' 等
        """
        if language in self.supported_languages:
            old_language = self.current_language
            self.current_language = language
            # 只有当语言确实发生变化时，才发送语言变化信号
            if old_language != language:
                self.language_changed.emit()
        else:
            # 如果指定的语言不支持，回退到系统语言
            self.current_language = self.get_system_language()
            logging.warning(f"Language {language} not supported, using system language: {self.current_language}")

    def translate(self, key: str, **kwargs) -> str:
        """
        翻译字符串
        
        根据当前语言和翻译键获取对应的翻译值，
        支持使用kwargs对翻译结果进行格式化，
        采用多级回退机制确保总能返回可用结果。

        Args:
            key: 翻译键，对应翻译文件中的键名
            **kwargs: 用于格式化翻译结果的参数

        Returns:
            str: 翻译后的字符串，如果找不到则返回键名
        """
        # 翻译查找优先级：
        # 1. 当前语言
        # 2. 英文（fallback）
        # 3. 翻译键本身（最终fallback）
        
        # 1. 尝试从当前语言中查找
        if (
            self.current_language in self.translations
            and key in self.translations[self.current_language]
        ):
            translation = self.translations[self.current_language][key]
        # 2. 如果当前语言找不到，尝试英文
        elif "en" in self.translations and key in self.translations["en"]:
            translation = self.translations["en"][key]
        # 3. 如果都找不到，返回键名作为最后选项
        else:
            logging.warning(
                f"Translation key '{key}' not found for language '{self.current_language}'"
            )
            return key

        # 检查是否需要对翻译结果进行格式化
        if "{" in translation and "}" in translation and kwargs:
            # 尝试格式化翻译结果
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                # 缺少格式化键时的处理
                logging.warning(
                    f"Missing format key '{e}' in translation for key '{key}'"
                )
                return translation  # 返回未格式化的原始翻译
            except IndexError as e:
                # 索引错误时的处理
                logging.warning(f"Index error in translation for key '{key}': {e}")
                return translation  # 返回未格式化的原始翻译
            except Exception as e:
                # 其他格式化错误时的处理
                logging.warning(
                    f"Unexpected error formatting translation for key '{key}': {e}"
                )
                return translation  # 返回未格式化的原始翻译
        else:
            # 不需要格式化，直接返回翻译结果
            return translation

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            Dict[str, str]: 语言代码到语言名称的映射字典
        """
        return self.supported_languages

    def get_current_language(self) -> str:
        """
        获取当前语言代码

        Returns:
            str: 当前语言代码，如 'zh-CN', 'en' 等
        """
        return self.current_language

    def get_language_display_name(self, language_code: str) -> str:
        """
        获取语言的显示名称
        
        根据语言代码获取对应的显示名称，
        如果找不到则返回语言代码本身。

        Args:
            language_code: 语言代码

        Returns:
            str: 语言显示名称，如 "简体中文"、"English" 等
        """
        return self.supported_languages.get(language_code, language_code)


# 创建国际化管理器实例，供全局使用
i18n = I18nManager()
