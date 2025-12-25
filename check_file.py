#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

# 读取文件内容
file_path = "AI_Talking/src/ui/discussion_tab.py"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 检查第475-485行
print("检查discussion_tab.py文件第475-485行：")
for i in range(474, min(485, len(lines))):
    line_num = i + 1
    line = lines[i]
    print(f"行{line_num}: {repr(line)}")
    
    # 检查是否包含中文逗号
    if '，' in line:
        print(f"  包含中文逗号，位置：{[pos for pos, char in enumerate(line) if char == '，']}")

# 检查整个文件中的中文逗号
print("\n文件中所有中文逗号位置：")
for i, line in enumerate(lines):
    if '，' in line:
        line_num = i + 1
        positions = [pos for pos, char in enumerate(line) if char == '，']
        print(f"行{line_num}: {positions}")
