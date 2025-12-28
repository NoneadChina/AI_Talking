#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有国际化文件的一致性
"""

import json
import os

# 获取i18n目录路径
i18n_dir = os.path.join(os.path.dirname(__file__), 'src', 'i8n')

# 获取所有i18n文件
i18n_files = [f for f in os.listdir(i18n_dir) if f.endswith('.json')]

# 读取所有i18n文件的内容
i18n_data = {}
for file in i18n_files:
    file_path = os.path.join(i18n_dir, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        i18n_data[file[:-5]] = json.load(f)

# 以英文文件为基准，获取所有预期的翻译键
expected_keys = set(i18n_data['en'].keys())
print(f"总共有 {len(expected_keys)} 个翻译键")
print(f"国际化文件列表: {list(i18n_data.keys())}")
print()

# 检查每个文件
for lang, data in i18n_data.items():
    actual_keys = set(data.keys())
    
    # 检查缺失的键
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        print(f"❌ {lang}.json 缺少 {len(missing_keys)} 个翻译键:")
        for key in sorted(missing_keys):
            print(f"   - {key}")
    else:
        print(f"✅ {lang}.json 包含所有翻译键")
    
    # 检查多余的键
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        print(f"⚠️  {lang}.json 包含 {len(extra_keys)} 个多余的翻译键:")
        for key in sorted(extra_keys):
            print(f"   - {key}")
    
    print()

# 检查所有文件共有的键
all_keys = set.intersection(*[set(data.keys()) for data in i18n_data.values()])
print(f"所有文件共有的键数量: {len(all_keys)}")
print()

# 检查键的数量统计
print("各文件键数量统计:")
for lang, data in i18n_data.items():
    print(f"{lang}.json: {len(data.keys())} 个键")
