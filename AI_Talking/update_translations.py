#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新翻译文件脚本，确保所有翻译文件包含简体中文文件中的所有翻译键
"""

import json
import os
import glob

def main():
    # 获取翻译文件目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    i18n_dir = os.path.join(script_dir, "src", "i8n")
    
    # 读取简体中文翻译文件（作为基准）
    zh_cn_path = os.path.join(i18n_dir, "zh-CN.json")
    with open(zh_cn_path, "r", encoding="utf-8") as f:
        zh_cn_data = json.load(f)
    
    # 获取所有翻译文件路径
    translation_files = glob.glob(os.path.join(i18n_dir, "*.json"))
    
    # 遍历每个翻译文件
    for file_path in translation_files:
        if file_path == zh_cn_path:
            continue  # 跳过简体中文文件
        
        print(f"处理文件: {os.path.basename(file_path)}")
        
        # 读取翻译文件
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 检查并添加缺失的翻译键
        missing_keys = []
        for key in zh_cn_data:
            if key not in data:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"  缺失 {len(missing_keys)} 个翻译键：{missing_keys}")
            
            # 添加缺失的翻译键，使用英文或默认值作为占位符
            for key in missing_keys:
                # 尝试从英文文件获取翻译，如果英文文件不存在或也没有该键，则使用键名作为默认值
                data[key] = key
            
            # 保存更新后的翻译文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"  文件已更新")
        else:
            print(f"  所有翻译键已存在")
    
    print("\n所有翻译文件已处理完成！")

if __name__ == "__main__":
    main()