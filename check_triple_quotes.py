#!/usr/bin/env python3

file_path = "d:/MyProgram/NONEAD/AI Talking/AI_Talking/src/ui/discussion_tab.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    triple_quotes = []
    in_triple_quote = False
    quote_type = None
    
    i = 0
    while i < len(content):
        if content[i:i+3] in ['"""', "'''" ]:
            quote_type = content[i:i+3]
            triple_quotes.append((i, quote_type))
            i += 3
        else:
            i += 1
    
    print(f"Found {len(triple_quotes)} triple quotes")
    print(f"Expected even number, got {len(triple_quotes)}")
    print("Triple quote positions:")
    for pos, qtype in triple_quotes:
        line = content[:pos].count('\n') + 1
        print(f"  Line {line}: {qtype} at position {pos}")
    
    if len(triple_quotes) % 2 != 0:
        print(f"\nERROR: Unbalanced triple quotes! Last one at line {line}")
    else:
        print("\nSUCCESS: All triple quotes are balanced")
        
except Exception as e:
    print(f"Error reading file: {e}")
