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
        from pathlib import Path
        
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用PyInstaller提供的临时目录
            self.translations_dir = os.path.join(sys._MEIPASS, "src", "i8n")
        else:
            # 开发环境，使用Path对象计算绝对路径
            self.translations_dir = str(Path(__file__).resolve().parent.parent / "i8n")

        # 翻译资源字典，存储所有语言的翻译数据
        # 结构: {语言代码: {翻译键: 翻译值}}
        self.translations: Dict[str, Dict[str, str]] = {}

        # 加载所有语言的翻译文件
        self._load_translations()
        
        # 验证所有翻译键的完整性
        invalid_keys = self.validate_all_translation_keys()
        if invalid_keys:
            logging.warning(
                f"Found {len(invalid_keys)} invalid translation keys: {', '.join(invalid_keys)}"
            )
            # 自动补全缺失的翻译键
            completed = self.complete_translations(save=True)
            if completed:
                logging.info(f"Automatically completed translations: {completed}")

        # 当前语言，默认使用系统语言
        self.current_language = self.get_system_language()

    def _load_translations(self):
        """
        从JSON文件加载所有语言的翻译数据
        
        遍历所有支持的语言，加载对应的JSON翻译文件，
        处理可能出现的异常情况，确保程序稳定性。
        """
        for lang_code in self.supported_languages:
            # 使用新的load_translation方法加载翻译
            self.load_translation(lang_code)

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
    
    def check_translations(self) -> Dict[str, Dict[str, list]]:
        """
        检查所有翻译文件的完整性和一致性
        
        比较所有翻译文件与参考语言（英语）的翻译键，
        找出每个语言文件中缺失的翻译键。

        Returns:
            Dict[str, Dict[str, list]]: 包含每个语言文件缺失键和多余键的字典
        """
        # 使用英语作为参考语言
        reference_lang = "en"
        if reference_lang not in self.translations:
            logging.error(f"Reference language '{reference_lang}' not found in translations")
            return {}
        
        reference_keys = set(self.translations[reference_lang].keys())
        results = {}
        
        for lang_code, translations in self.translations.items():
            lang_keys = set(translations.keys())
            
            # 缺失的翻译键
            missing_keys = reference_keys - lang_keys
            # 多余的翻译键
            extra_keys = lang_keys - reference_keys
            
            if missing_keys or extra_keys:
                results[lang_code] = {
                    "missing": sorted(list(missing_keys)),
                    "extra": sorted(list(extra_keys))
                }
        
        return results
    
    def complete_translations(self, save: bool = False) -> Dict[str, int]:
        """
        自动补全所有翻译文件中缺失的翻译键
        
        使用参考语言（英语）的翻译作为默认值，
        补全其他语言文件中缺失的翻译键。

        Args:
            save (bool): 是否将补全后的翻译保存到文件

        Returns:
            Dict[str, int]: 包含每种语言补全的翻译键数量的字典
        """
        # 使用英语作为参考语言
        reference_lang = "en"
        if reference_lang not in self.translations:
            logging.error(f"Reference language '{reference_lang}' not found in translations")
            return {}
        
        reference_translations = self.translations[reference_lang]
        completed_count = {}
        
        for lang_code, translations in self.translations.items():
            if lang_code == reference_lang:
                continue  # 跳过参考语言
            
            missing_keys = set(reference_translations.keys()) - set(translations.keys())
            if missing_keys:
                completed_count[lang_code] = 0
                for key in missing_keys:
                    # 使用参考语言的翻译作为默认值
                    self.translations[lang_code][key] = reference_translations[key]
                    completed_count[lang_code] += 1
                
                logging.info(f"Completed {completed_count[lang_code]} missing translations for language: {lang_code}")
        
        # 如果需要保存到文件
        if save:
            self._save_translations()
        
        return completed_count
    
    def _save_translations(self):
        """
        将当前加载的翻译保存到对应的JSON文件
        """
        for lang_code, translations in self.translations.items():
            try:
                file_path = os.path.join(self.translations_dir, f"{lang_code}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                logging.info(f"Saved translations to file: {file_path}")
            except Exception as e:
                logging.error(f"Error saving translations for language {lang_code}: {e}")
    
    def validate_translation_key(self, key: str) -> bool:
        """
        验证翻译键是否存在于所有支持的语言文件中
        
        Args:
            key (str): 要验证的翻译键

        Returns:
            bool: 如果翻译键存在于所有支持的语言文件中则返回True，否则返回False
        """
        for lang_code in self.supported_languages:
            if lang_code in self.translations:
                if key not in self.translations[lang_code]:
                    logging.warning(f"Translation key '{key}' not found in language '{lang_code}'")
                    return False
        return True
    
    def validate_all_translation_keys(self) -> list:
        """
        验证所有翻译键是否存在于所有翻译文件中
        
        Returns:
            list: 包含所有缺失翻译键的列表
        """
        # 使用英语作为参考语言
        reference_lang = "en"
        if reference_lang not in self.translations:
            logging.error(f"Reference language '{reference_lang}' not found in translations")
            return []
        
        reference_keys = self.translations[reference_lang].keys()
        invalid_keys = []
        
        for key in reference_keys:
            if not self.validate_translation_key(key):
                invalid_keys.append(key)
        
        return invalid_keys
    
    def load_translation(self, lang_code: str, incremental: bool = False) -> bool:
        """
        加载指定语言的翻译文件
        
        Args:
            lang_code (str): 语言代码
            incremental (bool): 是否增量加载（只加载新增的翻译键）

        Returns:
            bool: 加载成功返回True，否则返回False
        """
        try:
            file_path = os.path.join(self.translations_dir, f"{lang_code}.json")
            with open(file_path, "r", encoding="utf-8") as f:
                new_translations = json.load(f)
            
            if incremental and lang_code in self.translations:
                # 增量加载，只添加新的翻译键
                existing_translations = self.translations[lang_code]
                new_keys = set(new_translations.keys()) - set(existing_translations.keys())
                if new_keys:
                    for key in new_keys:
                        existing_translations[key] = new_translations[key]
                    logging.info(f"Incrementally loaded {len(new_keys)} new translations for language: {lang_code}")
            else:
                # 完整加载
                self.translations[lang_code] = new_translations
                logging.info(f"Loaded translations for language: {lang_code}")
            
            return True
        except FileNotFoundError:
            logging.error(f"Translation file not found for language: {lang_code}")
            self.translations[lang_code] = {}
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing translation file for language {lang_code}: {e}")
            self.translations[lang_code] = {}
        except Exception as e:
            logging.error(f"Unexpected error loading translations for language {lang_code}: {e}")
            self.translations[lang_code] = {}
        
        return False
    
    def reload_translations(self, incremental: bool = False) -> None:
        """
        重新加载所有翻译文件
        
        Args:
            incremental (bool): 是否增量加载
        """
        for lang_code in self.supported_languages:
            self.load_translation(lang_code, incremental)


# 创建国际化管理器实例，供全局使用
i18n = I18nManager()
