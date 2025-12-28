#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查国际化文件，确保所有翻译键完整且一致
"""

import os
import json
from collections import defaultdict

def check_i18n_keys():
    i18n_dir = os.path.join(os.path.dirname(__file__), "src", "i8n")
    
    # 获取所有翻译文件
    translation_files = [f for f in os.listdir(i18n_dir) if f.endswith(".json")]
    
    if not translation_files:
        print("未找到翻译文件")
        return
    
    print(f"找到 {len(translation_files)} 个翻译文件:")
    for f in translation_files:
        print(f"  - {f}")
    print()
    
    # 读取所有翻译文件
    translations = {}
    for f in translation_files:
        file_path = os.path.join(i18n_dir, f)
        with open(file_path, "r", encoding="utf-8") as fp:
            translations[f] = json.load(fp)
    
    # 获取所有翻译键
    all_keys = set()
    for file_name, trans in translations.items():
        all_keys.update(trans.keys())
    
    print(f"总共有 {len(all_keys)} 个翻译键")
    print()
    
    # 检查每个文件的键是否完整
    missing_keys = defaultdict(list)
    extra_keys = defaultdict(list)
    
    for file_name, trans in translations.items():
        file_keys = set(trans.keys())
        
        # 检查缺失的键
        missing = all_keys - file_keys
        if missing:
            missing_keys[file_name].extend(sorted(missing))
        
        # 检查额外的键
        extra = file_keys - all_keys
        if extra:
            extra_keys[file_name].extend(sorted(extra))
    
    # 输出结果
    if missing_keys:
        print("=== 缺失的翻译键 ===")
        for file_name, keys in missing_keys.items():
            print(f"{file_name} 缺失 {len(keys)} 个键:")
            for key in keys:
                print(f"  - {key}")
            print()
    else:
        print("✅ 所有文件都包含完整的翻译键")
    
    if extra_keys:
        print("=== 额外的翻译键 ===")
        for file_name, keys in extra_keys.items():
            print(f"{file_name} 有 {len(keys)} 个额外的键:")
            for key in keys:
                print(f"  - {key}")
            print()
    else:
        print("✅ 所有文件的键都一致，没有额外的键")
    
    # 检查翻译值是否为空
    empty_values = defaultdict(list)
    
    for file_name, trans in translations.items():
        for key, value in trans.items():
            if not value:
                empty_values[file_name].append(key)
    
    if empty_values:
        print("=== 空值翻译键 ===")
        for file_name, keys in empty_values.items():
            print(f"{file_name} 有 {len(keys)} 个空值翻译键:")
            for key in keys:
                print(f"  - {key}")
            print()
    else:
        print("✅ 所有翻译值都不为空")
    
    print("检查完成！")

if __name__ == "__main__":
    check_i18n_keys()
