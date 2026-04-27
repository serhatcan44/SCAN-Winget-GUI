from __future__ import annotations

import json
import os


LanguageTexts = dict[str, str]


LANGUAGE_FILE = os.path.join(os.path.dirname(__file__), "languages.json")
DEFAULT_LANGUAGE = "Türkçe"


def load_language(language: str) -> LanguageTexts:
    if not os.path.exists(LANGUAGE_FILE):
        raise FileNotFoundError(f"languages.json dosyası bulunamadı: {LANGUAGE_FILE}")
    with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(language, data.get(DEFAULT_LANGUAGE, {}))


def get_theme_values(language: str) -> list[str]:
    theme_values = {
        "Türkçe": ["Koyu", "Açık"],
        "English": ["Dark", "Light"],
        "Русский": ["Тёмная", "Светлая"],
        "Deutsch": ["Dunkel", "Hell"],
        "中文": ["深色", "浅色"],
        "Español": ["Oscuro", "Claro"],
        "العربية": ["داكن", "فاتح"],
    }
    return theme_values.get(language, ["Dark", "Light"])
