import json
import os
import logging

# Set up logging to match the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_i18n_loading():
    """Simulate the exact loading process from i18n_manager.py"""
    
    # Supported languages (same as in i18n_manager.py)
    supported_languages = {
        "zh-CN": "简体中文",
        "zh-TW": "繁体中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "de": "Deutsch",
        "es": "Español",
        "fr": "Français",
        "ar": "العربية",
        "ru": "Русский",
    }
    
    # Use the correct translations directory (relative to current working directory)
    translations_dir = os.path.join(
        "src", "i8n"
    )
    
    logging.info(f"Translations directory: {translations_dir}")
    
    translations = {}
    
    # Load translations exactly as in i18n_manager.py
    for lang_code in supported_languages:
        try:
            file_path = os.path.join(translations_dir, f"{lang_code}.json")
            logging.info(f"Attempting to load: {file_path}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logging.info(f"Read {len(content)} characters from {lang_code}.json")
                # Try to load the content
                translations[lang_code] = json.loads(content)
            logging.info(f"Loaded translations for language: {lang_code}")
        except FileNotFoundError:
            logging.error(f"Translation file not found for language: {lang_code}")
            translations[lang_code] = {}
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing translation file for language {lang_code}: {e}")
            logging.error(f"Error position: line {e.lineno}, column {e.colno}")
            # Show the problematic line
            try:
                lines = content.split('\n')
                if e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    logging.error(f"Problematic line {e.lineno}: {repr(problem_line)}")
                    logging.error(f"Line length: {len(problem_line)} characters")
                    # Show characters around the problematic column
                    if e.colno <= len(problem_line):
                        start = max(0, e.colno - 5)
                        end = min(len(problem_line), e.colno + 5)
                        logging.error(f"Characters around column {e.colno}: {repr(problem_line[start:end])}")
            except:
                logging.error("Failed to show problematic line")
            translations[lang_code] = {}
        except Exception as e:
            logging.error(f"Unexpected error loading translations for language {lang_code}: {e}")
            translations[lang_code] = {}

if __name__ == "__main__":
    simulate_i18n_loading()
