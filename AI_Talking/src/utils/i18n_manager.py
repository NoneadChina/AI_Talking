# -*- coding: utf-8 -*-
"""
国际化管理模块，用于处理应用程序的多语言支持
"""

import os
import json
import logging
from typing import Dict, Optional
from PyQt5.QtCore import QLocale, QObject, pyqtSignal


class I18nManager(QObject):
    """
    国际化管理器，负责处理应用程序的多语言支持
    """

    # 语言变化信号
    language_changed = pyqtSignal()

    def __init__(self):
        """
        初始化国际化管理器
        """
        super().__init__()

        # 支持的语言列表
        self.supported_languages = {
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            "en": "English",
            "ja": "日本語",
        }

        # 翻译资源目录
        self.translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "i8n"
        )

        # 翻译资源
        self.translations: Dict[str, Dict[str, str]] = {}

        # 加载所有语言的翻译文件
        self._load_translations()

        # 当前语言
        self.current_language = self.get_system_language()

    def _load_translations(self):
        """
        从JSON文件加载所有语言的翻译数据
        """
        for lang_code in self.supported_languages:
            try:
                file_path = os.path.join(self.translations_dir, f"{lang_code}.json")
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
                logging.info(f"Loaded translations for language: {lang_code}")
            except FileNotFoundError:
                logging.error(f"Translation file not found for language: {lang_code}")
                # 如果文件不存在，使用空字典
                self.translations[lang_code] = {}
            except json.JSONDecodeError as e:
                logging.error(
                    f"Error parsing translation file for language {lang_code}: {e}"
                )
                # 如果解析错误，使用空字典
                self.translations[lang_code] = {}
            except Exception as e:
                logging.error(
                    f"Unexpected error loading translations for language {lang_code}: {e}"
                )
                # 如果发生其他错误，使用空字典
                self.translations[lang_code] = {}

    def get_system_language(self) -> str:
        """
        获取操作系统语言

        Returns:
            str: 语言代码，如 'zh-CN', 'en', 'ja' 等
        """
        locale = QLocale.system().name()
        # 将下划线替换为连字符，确保语言代码格式统一
        locale = locale.replace("_", "-")
        # 简化语言代码，如将 'zh-CN' 简化为 'zh'，但保留中文繁体的区分
        if locale.startswith("zh"):
            return locale  # 保留 'zh-CN' 或 'zh-TW'
        else:
            return locale.split("-")[0]  # 其他语言只保留主语言代码，如 'en-US' -> 'en'

    def set_language(self, language: str):
        """
        设置当前语言

        Args:
            language: 语言代码，如 'zh-CN', 'en', 'ja' 等
        """
        if language in self.supported_languages:
            old_language = self.current_language
            self.current_language = language
            # 发送语言变化信号
            if old_language != language:
                self.language_changed.emit()
        else:
            # 如果指定的语言不支持，使用系统语言
            self.current_language = self.get_system_language()

    def translate(self, key: str, **kwargs) -> str:
        """
        翻译字符串

        Args:
            key: 翻译键
            **kwargs: 用于格式化翻译结果的参数

        Returns:
            str: 翻译后的字符串，如果找不到则返回键名
        """
        # 先尝试当前语言
        if (
            self.current_language in self.translations
            and key in self.translations[self.current_language]
        ):
            translation = self.translations[self.current_language][key]
        # 如果当前语言找不到，尝试英文
        elif "en" in self.translations and key in self.translations["en"]:
            translation = self.translations["en"][key]
        # 如果都找不到，返回键名
        else:
            logging.warning(
                f"Translation key '{key}' not found for language '{self.current_language}'"
            )
            return key

        # 检查是否需要格式化
        if "{" in translation and "}" in translation and kwargs:
            # 格式化翻译结果
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                logging.warning(
                    f"Missing format key '{e}' in translation for key '{key}'"
                )
                return translation
            except IndexError as e:
                logging.warning(f"Index error in translation for key '{key}': {e}")
                return translation
            except Exception as e:
                logging.warning(
                    f"Unexpected error formatting translation for key '{key}': {e}"
                )
                return translation
        else:
            return translation

    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            Dict[str, str]: 语言代码到语言名称的映射
        """
        return self.supported_languages

    def get_current_language(self) -> str:
        """
        获取当前语言代码

        Returns:
            str: 当前语言代码
        """
        return self.current_language

    def get_language_display_name(self, language_code: str) -> str:
        """
        获取语言的显示名称

        Args:
            language_code: 语言代码

        Returns:
            str: 语言显示名称
        """
        return self.supported_languages.get(language_code, language_code)


# 创建国际化管理器实例
i18n = I18nManager()
