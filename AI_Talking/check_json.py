#!/usr/bin/env python3
import json
import sys

# 默认检查简体中文，如果提供了参数则检查指定语言
lang = sys.argv[1] if len(sys.argv) > 1 else 'zh-CN'

file_path = f'src/i8n/{lang}.json'
with open(file_path, 'r', encoding='utf-8') as f:
    try:
        data = json.load(f)
        print(f'{lang} JSON格式正确')
        print(f'包含 {len(data)} 个键')
    except json.JSONDecodeError as e:
        print(f'{lang} JSON格式错误: {e}')
