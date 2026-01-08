# -*- coding: utf-8 -*-
"""
检查翻译文件，确保所有翻译键都存在，与简体中文文件保持一致
"""

import os
import json
import logging
from typing import Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 翻译文件目录
translations_dir = "src/i8n"
# 支持的语言列表
supported_languages = ["zh-CN", "zh-TW", "en", "ja", "ko", "de", "es", "fr", "ar", "ru"]

def load_translation(file_path: str) -> Dict[str, str]:
    """加载翻译文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading translation file {file_path}: {e}")
        return {}

def save_translation(file_path: str, translations: Dict[str, str]) -> None:
    """保存翻译文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved translations to {file_path}")
    except Exception as e:
        logger.error(f"Error saving translation file {file_path}: {e}")

def check_translations() -> None:
    """检查所有翻译文件，确保与简体中文文件的翻译键保持一致"""
    # 加载简体中文翻译作为参考
    zh_cn_file = os.path.join(translations_dir, "zh-CN.json")
    zh_cn_translations = load_translation(zh_cn_file)
    
    if not zh_cn_translations:
        logger.error(f"Failed to load Simplified Chinese translations from {zh_cn_file}")
        return
    
    logger.info(f"Loaded Simplified Chinese translations, found {len(zh_cn_translations)} keys")
    
    # 加载英语翻译作为默认值来源
    en_file = os.path.join(translations_dir, "en.json")
    en_translations = load_translation(en_file)
    
    if not en_translations:
        logger.error(f"Failed to load English translations from {en_file}")
        return
    
    logger.info(f"Loaded English translations, found {len(en_translations)} keys")
    
    # 检查每个语言文件
    for lang_code in supported_languages:
        lang_file = os.path.join(translations_dir, f"{lang_code}.json")
        lang_translations = load_translation(lang_file)
        
        logger.info(f"Checking {lang_code} translations, found {len(lang_translations)} keys")
        
        # 检查是否有缺失的翻译键
        missing_keys = set(zh_cn_translations.keys()) - set(lang_translations.keys())
        if missing_keys:
            logger.warning(f"Found {len(missing_keys)} missing keys in {lang_code}: {missing_keys}")
            
            # 添加缺失的翻译键，使用英语作为默认值
            for key in missing_keys:
                if key in en_translations:
                    lang_translations[key] = en_translations[key]
                    logger.info(f"Added missing key '{key}' to {lang_code} with English default value")
                else:
                    lang_translations[key] = key  # 使用键名作为最后的默认值
                    logger.warning(f"Added missing key '{key}' to {lang_code} with key name as default")
            
            # 保存更新后的翻译文件
            save_translation(lang_file, lang_translations)
            logger.info(f"Updated {lang_code} translations, now has {len(lang_translations)} keys")
        else:
            logger.info(f"{lang_code} translations are complete")
        
        # 检查是否有多余的翻译键
        extra_keys = set(lang_translations.keys()) - set(zh_cn_translations.keys())
        if extra_keys:
            logger.warning(f"Found {len(extra_keys)} extra keys in {lang_code}: {extra_keys}")
            
            # 移除多余的翻译键
            for key in extra_keys:
                del lang_translations[key]
                logger.info(f"Removed extra key '{key}' from {lang_code}")
            
            # 保存更新后的翻译文件
            save_translation(lang_file, lang_translations)
            logger.info(f"Updated {lang_code} translations, removed {len(extra_keys)} extra keys")

if __name__ == "__main__":
    check_translations()
