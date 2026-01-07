#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查翻译文件的键一致性，以中文(zh-CN.json)为基准
"""

import os
import json

# 翻译文件目录
translations_dir = os.path.join(os.path.dirname(__file__), "src", "i8n")

# 支持的语言列表
supported_languages = ["zh-CN", "zh-TW", "en", "ja", "ko", "de", "es", "fr", "ar", "ru"]


def load_translation_file(lang_code):
    """加载翻译文件"""
    file_path = os.path.join(translations_dir, f"{lang_code}.json")
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return None


def check_consistency(base_lang="zh-CN"):
    """检查所有翻译文件与基准语言的一致性"""
    print(f"Checking translation consistency with base language: {base_lang}")
    print("=" * 50)
    
    # 加载基准语言
    base_translations = load_translation_file(base_lang)
    if not base_translations:
        return
    
    base_keys = set(base_translations.keys())
    print(f"Base language ({base_lang}) has {len(base_keys)} keys")
    print()
    
    # 检查其他语言
    results = {}
    for lang in supported_languages:
        if lang == base_lang:
            continue
        
        translations = load_translation_file(lang)
        if not translations:
            continue
        
        lang_keys = set(translations.keys())
        missing_keys = base_keys - lang_keys
        extra_keys = lang_keys - base_keys
        
        results[lang] = {
            "total_keys": len(lang_keys),
            "missing_keys": missing_keys,
            "extra_keys": extra_keys,
            "consistent": len(missing_keys) == 0 and len(extra_keys) == 0
        }
        
        print(f"Language: {lang}")
        print(f"  Total keys: {len(lang_keys)}")
        print(f"  Missing keys: {len(missing_keys)}")
        if missing_keys:
            print(f"    {', '.join(missing_keys)}")
        print(f"  Extra keys: {len(extra_keys)}")
        if extra_keys:
            print(f"    {', '.join(extra_keys)}")
        print(f"  Consistent: {'✓' if results[lang]['consistent'] else '✗'}")
        print()
    
    return results


def sync_translations(base_lang="zh-CN"):
    """同步所有翻译文件，确保键集合与基准语言一致"""
    print(f"Syncing translations with base language: {base_lang}")
    print("=" * 50)
    
    # 加载基准语言
    base_translations = load_translation_file(base_lang)
    if not base_translations:
        return
    
    base_keys = set(base_translations.keys())
    
    for lang in supported_languages:
        if lang == base_lang:
            continue
        
        translations = load_translation_file(lang)
        if not translations:
            continue
        
        lang_keys = set(translations.keys())
        missing_keys = base_keys - lang_keys
        extra_keys = lang_keys - base_keys
        
        # 移除多余的键
        for key in extra_keys:
            del translations[key]
        
        # 添加缺失的键，使用键名作为默认值
        for key in missing_keys:
            translations[key] = key
        
        # 按基准语言的顺序排序键
        sorted_translations = {key: translations.get(key, key) for key in base_translations}
        
        # 保存同步后的文件
        file_path = os.path.join(translations_dir, f"{lang}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted_translations, f, ensure_ascii=False, indent=2)
        
        print(f"Synced {lang}.json: {len(sorted_translations)} keys")
    
    print()
    print("Sync completed!")


if __name__ == "__main__":
    # 先检查一致性
    results = check_consistency()
    
    # 询问是否同步
    sync = input("Would you like to sync all translation files to match the base language? (y/n): ")
    if sync.lower() == "y":
        sync_translations()
        # 再次检查以验证同步结果
        print("\nVerifying sync results...")
        check_consistency()
    else:
        print("Sync aborted.")
