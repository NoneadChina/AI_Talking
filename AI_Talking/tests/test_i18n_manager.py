# -*- coding: utf-8 -*-
"""
国际化管理器单元测试
"""

import os
import tempfile
import json
import pytest
import shutil
from pathlib import Path
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.i18n_manager import I18nManager


class TestI18nManager:
    """
    测试国际化管理器
    """
    
    def setup_method(self):
        """
        每个测试方法前的设置
        """
        # 创建临时目录用于测试翻译文件
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建参考语言（英语）翻译文件
        self.en_translations = {
            "app_title": "AI Talking",
            "tab_chat": "Chat",
            "tab_discussion": "Discussion",
            "tab_debate": "Debate",
            "btn_send": "Send"
        }
        
        # 创建不完整的中文翻译文件
        self.zh_cn_translations = {
            "app_title": "AI 对话",
            "tab_chat": "聊天",
            # 缺少 tab_discussion 和 tab_debate
            "btn_send": "发送"
        }
        
        # 创建多余键的日语翻译文件
        self.ja_translations = {
            "app_title": "AI トーキング",
            "tab_chat": "チャット",
            "tab_discussion": "ディスカッション",
            "tab_debate": "ディベート",
            "btn_send": "送信",
            "extra_key": "余分なキー"  # 多余的键
        }
        
        # 写入翻译文件
        with open(os.path.join(self.temp_dir, "en.json"), "w", encoding="utf-8") as f:
            json.dump(self.en_translations, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.temp_dir, "zh-CN.json"), "w", encoding="utf-8") as f:
            json.dump(self.zh_cn_translations, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.temp_dir, "ja.json"), "w", encoding="utf-8") as f:
            json.dump(self.ja_translations, f, ensure_ascii=False, indent=2)
        
        # 保存原始的translations_dir
        self.original_translations_dir = None
    
    def teardown_method(self):
        """
        每个测试方法后的清理
        """
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
        
    def test_check_translations(self):
        """
        测试检查翻译文件的完整性
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 重新加载翻译文件
        i18n._load_translations()
        
        # 检查翻译文件
        results = i18n.check_translations()
        
        # 验证结果
        assert "zh-CN" in results
        assert "missing" in results["zh-CN"]
        assert "tab_discussion" in results["zh-CN"]["missing"]
        assert "tab_debate" in results["zh-CN"]["missing"]
        
        assert "ja" in results
        assert "extra" in results["ja"]
        assert "extra_key" in results["ja"]["extra"]
        
    def test_complete_translations(self):
        """
        测试自动补全翻译文件
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 重新加载翻译文件
        i18n._load_translations()
        
        # 补全翻译文件
        completed = i18n.complete_translations(save=False)
        
        # 验证结果
        assert "zh-CN" in completed
        assert completed["zh-CN"] == 2  # 补全了2个键
        
        # 检查补全后的翻译
        assert "tab_discussion" in i18n.translations["zh-CN"]
        assert "tab_debate" in i18n.translations["zh-CN"]
        # 补全的翻译应该使用英语作为默认值
        assert i18n.translations["zh-CN"]["tab_discussion"] == "Discussion"
        assert i18n.translations["zh-CN"]["tab_debate"] == "Debate"
    
    def test_validate_translation_key(self):
        """
        测试验证翻译键
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 只保留我们创建的翻译文件对应的语言
        i18n.supported_languages = {
            "en": "English",
            "zh-CN": "简体中文",
            "ja": "日本語"
        }
        
        # 重新加载翻译文件
        i18n._load_translations()
        
        # 验证存在的键
        assert i18n.validate_translation_key("app_title") is True
        
        # 验证不存在的键
        assert i18n.validate_translation_key("non_existent_key") is False
    
    def test_validate_all_translation_keys(self):
        """
        测试验证所有翻译键
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 只保留我们创建的翻译文件对应的语言
        i18n.supported_languages = {
            "en": "English",
            "zh-CN": "简体中文",
            "ja": "日本語"
        }
        
        # 重新加载翻译文件
        i18n._load_translations()
        
        # 验证所有翻译键
        invalid_keys = i18n.validate_all_translation_keys()
        
        # 应该有2个无效键
        assert len(invalid_keys) == 2
        assert "tab_discussion" in invalid_keys
        assert "tab_debate" in invalid_keys
    
    def test_load_translation_incremental(self):
        """
        测试增量加载翻译文件
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 初始加载中文翻译
        i18n.load_translation("zh-CN")
        
        # 检查初始加载的翻译键数量
        initial_keys_count = len(i18n.translations["zh-CN"])
        
        # 修改中文翻译文件，添加新键
        updated_zh_cn_translations = self.zh_cn_translations.copy()
        updated_zh_cn_translations["tab_discussion"] = "讨论"
        updated_zh_cn_translations["new_key"] = "新键"
        
        with open(os.path.join(self.temp_dir, "zh-CN.json"), "w", encoding="utf-8") as f:
            json.dump(updated_zh_cn_translations, f, ensure_ascii=False, indent=2)
        
        # 增量加载中文翻译
        i18n.load_translation("zh-CN", incremental=True)
        
        # 检查增量加载后的翻译键数量
        incremental_keys_count = len(i18n.translations["zh-CN"])
        
        # 应该增加了2个新键
        assert incremental_keys_count == initial_keys_count + 2
        assert "tab_discussion" in i18n.translations["zh-CN"]
        assert "new_key" in i18n.translations["zh-CN"]
    
    def test_reload_translations(self):
        """
        测试重新加载所有翻译文件
        """
        # 创建I18nManager实例
        i18n = I18nManager()
        
        # 替换translations_dir为临时目录
        i18n.translations_dir = self.temp_dir
        
        # 初始加载翻译
        i18n._load_translations()
        
        # 修改英语翻译文件
        updated_en_translations = self.en_translations.copy()
        updated_en_translations["new_key"] = "New Key"
        
        with open(os.path.join(self.temp_dir, "en.json"), "w", encoding="utf-8") as f:
            json.dump(updated_en_translations, f, ensure_ascii=False, indent=2)
        
        # 重新加载所有翻译文件
        i18n.reload_translations()
        
        # 检查重新加载后的翻译
        assert "new_key" in i18n.translations["en"]
        assert i18n.translations["en"]["new_key"] == "New Key"
