import json
import os

def check_json_file(file_path):
    print(f"Checking {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ {file_path} is valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"✗ Error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error in {file_path}: {e}")
        return False

# Check all language files
language_files = [
    'src/i8n/ar.json',
    'src/i8n/ru.json',
    'src/i8n/zh-CN.json',
    'src/i8n/zh-TW.json',
    'src/i8n/en.json',
    'src/i8n/ja.json',
    'src/i8n/ko.json',
    'src/i8n/de.json',
    'src/i8n/es.json',
    'src/i8n/fr.json'
]

print("Checking all translation files...")
print("=" * 50)

for file in language_files:
    check_json_file(file)
