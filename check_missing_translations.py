import json
import os

# 获取翻译文件路径
i18n_dir = r"d:\MyProgram\GitCode\AI_Talking\AI_Talking\src\utils\i8n"

# 读取所有翻译文件
translation_files = {
    "en": os.path.join(i18n_dir, "en.json"),
    "zh-CN": os.path.join(i18n_dir, "zh-CN.json"),
    "zh-TW": os.path.join(i18n_dir, "zh-TW.json"),
    "ja": os.path.join(i18n_dir, "ja.json")
}

translations = {}
for lang, file_path in translation_files.items():
    with open(file_path, "r", encoding="utf-8") as f:
        translations[lang] = json.load(f)

# 获取英文文件中的所有键作为基准
english_keys = set(translations["en"].keys())

# 检查每个语言文件是否缺少键
for lang, lang_translations in translations.items():
    if lang == "en":
        continue
    
    lang_keys = set(lang_translations.keys())
    missing_keys = english_keys - lang_keys
    
    if missing_keys:
        print(f"Language {lang} is missing the following keys:")
        for key in sorted(missing_keys):
            print(f"  - {key}")
    else:
        print(f"Language {lang} has all keys.")

# 检查键的数量是否一致
for lang, lang_translations in translations.items():
    print(f"\n{lang} has {len(lang_translations)} keys.")
