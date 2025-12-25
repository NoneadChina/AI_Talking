import json
import os

def check_json_detailed(file_path, line_num, col_num):
    print(f"\nDetailed check for {file_path} at line {line_num}, column {col_num}:")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count lines to find the specific position
        lines = content.split('\n')
        if line_num <= len(lines):
            target_line = lines[line_num - 1]
            print(f"Line {line_num}: {repr(target_line)}")
            print(f"Line length: {len(target_line)} characters")
            
            # Show characters around the problematic column
            if col_num <= len(target_line):
                start = max(0, col_num - 5)
                end = min(len(target_line), col_num + 5)
                print(f"Characters around column {col_num}: {repr(target_line[start:end])}")
                
                # Show character codes
                print("Character codes:")
                for i in range(start, end):
                    char = target_line[i]
                    print(f"  [{i}] {repr(char)} (0x{ord(char):04X})")
            else:
                print(f"Column {col_num} is beyond line length {len(target_line)}")
        else:
            print(f"Line {line_num} is beyond file length {len(lines)}")
        
        # Try to load the file to confirm
        print("\nTrying to load the file...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✓ File loaded successfully!")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ JSONDecodeError: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

# Check the problematic files at the reported positions
check_json_detailed('src/i8n/ar.json', 227, 36)
check_json_detailed('src/i8n/ru.json', 227, 36)
