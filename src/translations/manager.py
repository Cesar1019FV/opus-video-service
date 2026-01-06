"""
Translation Manager
Handles loading of locales and string retrieval.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

class Translator:
    """
    Manages application translations.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.current_lang = "en"
        self.translations = {}
        self.locales_dir = Path(__file__).parent
        self.settings_file = self.locales_dir / "settings.json"
        
        self.load_settings()
        self.load_translations()
        self._initialized = True

    def load_settings(self):
        """Load language from settings file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_lang = settings.get("language", "en")
            except Exception:
                self.current_lang = "en"
        else:
            self.current_lang = "en"

    def save_settings(self, lang: str):
        """Save selected language to settings file"""
        self.current_lang = lang
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({"language": lang}, f)
        except Exception as e:
            print(f"Error saving language settings: {e}")

    def load_translations(self):
        """Load the translation dictionary for the current language"""
        try:
            if self.current_lang == "es":
                from .es import TRANSLATIONS
            else:
                from .en import TRANSLATIONS
            self.translations = TRANSLATIONS
        except ImportError:
            # Fallback to English if something goes wrong
            from .en import TRANSLATIONS
            self.translations = TRANSLATIONS

    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key with optional formatting.
        
        Args:
            key: Translation key
            **kwargs: Values for string formatting
            
        Returns:
            Translated and formatted string
        """
        text = self.translations.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

    def set_language(self, lang: str):
        """Change language and reload translations"""
        self.save_settings(lang)
        self.load_translations()


# Global translator instance
_translator = None

def get_translator() -> Translator:
    """Get the global translator instance"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator
