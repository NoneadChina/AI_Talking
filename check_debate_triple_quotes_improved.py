#!/usr/bin/env python3

file_path = "d:/MyProgram/NONEAD/AI Talking/AI_Talking/src/ui/debate_tab.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    triple_quotes = []
    
    i = 0
    while i < len(content):
        if content[i:i+3] in ['"""', "'''" ]:
            quote_type = content[i:i+3]
            line = content[:i].count('\n') + 1
            triple_quotes.append((line, quote_type, i))
            i += 3
        else:
            i += 1
    
    print(f"Found {len(triple_quotes)} triple quotes in debate_tab.py")
    print(f"Expected even number, got {len(triple_quotes)}")
    
    # Check matching pairs
    print(f"\nTriple quote pairs:")
    for i in range(0, len(triple_quotes), 2):
        if i+1 < len(triple_quotes):
            open_line, open_type, open_pos = triple_quotes[i]
            close_line, close_type, close_pos = triple_quotes[i+1]
            if open_type == close_type:
                print(f"  Lines {open_line}-{close_line}: {open_type} (match)")
            else:
                print(f"  Lines {open_line}-{close_line}: {open_type} -> {close_type} (mismatch!)")
        else:
            open_line, open_type, open_pos = triple_quotes[i]
            print(f"  Line {open_line}: {open_type} (UNMATCHED!)")
    
    if len(triple_quotes) % 2 != 0:
        print("\nERROR: Unbalanced triple quotes!")
    else:
        print("\nSUCCESS: All triple quotes are balanced")
    
except Exception as e:
    print(f"Error reading file: {e}")
