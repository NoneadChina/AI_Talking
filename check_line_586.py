#!/usr/bin/env python3

file_path = "d:/MyProgram/NONEAD/AI Talking/AI_Talking/src/ui/debate_tab.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    line_586 = lines[585]  # 0-indexed
    print(f"Line 586: {repr(line_586)}")
    print(f"Length: {len(line_586)}")
    print(f"Characters:")
    for i, char in enumerate(line_586):
        print(f"  {i}: '{char}' (U+{ord(char):04X})")
    
    # Check line 584-588
    print(f"\nLines 584-588:")
    for i in range(583, 588):
        line = lines[i]
        print(f"Line {i+1}: {repr(line.strip())}")
        for j, char in enumerate(line.strip()):
            if char in ['"', "'", '，', '。', '；', '：', '（', '）', '【', '】']:
                print(f"    Char {j}: '{char}' (U+{ord(char):04X})")
    
except Exception as e:
    print(f"Error reading file: {e}")
