#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有翻译文件的完整性，比较它们与英文翻译文件的翻译键是否一致
"""

import os
import json
import sys

# 获取当前脚本所在目录的父目录，即项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
i18n_dir = os.path.join(project_root, 'src', 'i8n')

# 读取英文翻译文件作为基准
en_file = os.path.join(i18n_dir, 'en.json')
with open(en_file, 'r', encoding='utf-8') as f:
    en_translations = json.load(f)

# 获取所有翻译键
en_keys = set(en_translations.keys())
print(f"英文翻译文件共有 {len(en_keys)} 个翻译键")

# 读取中文简体翻译文件作为参考
zh_cn_file = os.path.join(i18n_dir, 'zh-CN.json')
with open(zh_cn_file, 'r', encoding='utf-8') as f:
    zh_cn_translations = json.load(f)

# 读取所有其他翻译文件
translation_files = [
    'zh-TW.json',  # 中文繁体
    'ja.json',      # 日文
    'ko.json',      # 韩文
    'de.json',      # 德文
    'es.json',      # 西班牙文
    'fr.json',      # 法文
    'ru.json',      # 俄文
    'ar.json'       # 阿拉伯文
]

missing_keys = {}

# 检查每个翻译文件的完整性
for file_name in translation_files:
    file_path = os.path.join(i18n_dir, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # 获取当前文件的翻译键
        current_keys = set(translations.keys())
        
        # 找出缺失的翻译键
        missing = en_keys - current_keys
        if missing:
            missing_keys[file_name] = missing
            print(f"\n{file_name} 缺失 {len(missing)} 个翻译键：")
            for key in sorted(missing):
                print(f"  - {key}: {en_translations[key]} (中文: {zh_cn_translations.get(key, '')})")
        else:
            print(f"\n{file_name} 翻译键完整")
    else:
        print(f"\n{file_name} 不存在")

# 补充缺失的翻译键
if missing_keys:
    print("\n开始补充缺失的翻译键...")
    
    for file_name, keys in missing_keys.items():
        file_path = os.path.join(i18n_dir, file_name)
        
        # 读取当前翻译文件
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # 补充缺失的翻译键，使用英文翻译作为默认值
        for key in keys:
            # 使用英文翻译作为默认值
            translations[key] = en_translations[key]
            print(f"{file_name}: 已添加翻译键 '{key}'，使用英文翻译作为默认值")
        
        # 保存更新后的翻译文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        
        print(f"\n已更新 {file_name}，添加了 {len(keys)} 个翻译键")
else:
    print("\n所有翻译文件都已完整，无需补充")

print("\n检查完成！")
