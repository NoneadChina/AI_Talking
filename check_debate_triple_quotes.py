#!/usr/bin/env python3

file_path = "AI_Talking/src/ui/debate_tab.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    triple_quotes = []
    
    i = 0
    while i < len(content):
        if content[i:i+3] in ['"""', "'''" ]:
            quote_type = content[i:i+3]
            triple_quotes.append((i, quote_type))
            i += 3
        else:
            i += 1
    
    print(f"Found {len(triple_quotes)} triple quotes in debate_tab.py")
    print(f"Expected even number, got {len(triple_quotes)}")
    
    if len(triple_quotes) % 2 != 0:
        print("ERROR: Unbalanced triple quotes!")
        
    # Check around line 596
    line_num = 596
    char_pos = content[:content.find('\n'*line_num)].count('\n')
    print(f"\nChecking around line {line_num}:")
    
    # Find the nearest triple quotes
    for pos, qtype in triple_quotes:
        line = content[:pos].count('\n') + 1
        if line <= line_num:
            print(f"  Opening {qtype} at line {line}")
            last_opening = (pos, qtype, line)
        else:
            print(f"  Closing {qtype} at line {line}")
            break
    
except Exception as e:
    print(f"Error reading file: {e}")
