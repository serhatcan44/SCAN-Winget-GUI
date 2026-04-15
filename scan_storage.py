from __future__ import annotations

import json
import logging
import os
import shutil
from typing import Any


HistoryItem = dict[str, str]
Settings = dict[str, str]


APP_NAME = "SCAN"
LEGACY_SETTINGS_DIR = r"C:\scanapp"
LOCALAPPDATA_DIR = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
SETTINGS_DIR = os.path.join(LOCALAPPDATA_DIR, APP_NAME)
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")
HISTORY_PATH = os.path.join(SETTINGS_DIR, "history.json")

logger = logging.getLogger(__name__)


def ensure_app_storage() -> None:
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
    except OSError as e:
        logger.error(f"Settings directory oluşturulamadı: {e}")
        raise
    legacy_settings_path = os.path.join(LEGACY_SETTINGS_DIR, "settings.json")
    if (not os.path.exists(SETTINGS_PATH)) and os.path.exists(legacy_settings_path):
        try:
            shutil.copy2(legacy_settings_path, SETTINGS_PATH)
            logger.info("Eski ayarlar yeni konuma taşındı.")
        except (OSError, IOError) as e:
            logger.warning(f"Eski ayarlar taşınamadı: {e}")


def load_json_file(path: str, default_value: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"Dosya bulunamadı, varsayılan değer kullanılıyor: {path}")
        return default_value
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode hatası {path}: {e}")
        # Backup'a başvur veya varsayılan döndür
        backup_path = path + ".backup"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    logger.info(f"Backup dosyasından yükleniyor: {backup_path}")
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        return default_value
    except (OSError, IOError) as e:
        logger.error(f"Dosya okuma hatası {path}: {e}")
        return default_value


def save_json_file(path: str, payload: Any) -> None:
    ensure_app_storage()
    # Backup al
    if os.path.exists(path):
        backup_path = path + ".backup"
        try:
            shutil.copy2(path, backup_path)
            logger.debug(f"Backup oluşturuldu: {backup_path}")
        except (OSError, IOError) as e:
            logger.warning(f"Backup oluşturulamadı: {e}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.debug(f"Dosya kaydedildi: {path}")
    except (OSError, IOError) as e:
        logger.error(f"Dosya kaydedilemedi {path}: {e}")
        raise


def load_settings() -> Settings:
    ensure_app_storage()
    if os.path.exists(SETTINGS_PATH):
        settings = load_json_file(SETTINGS_PATH, {})
        settings.setdefault("language", "Türkçe")
        settings.setdefault("Theme", "Dark")
        return settings
    return {"language": "Türkçe", "Theme": "Dark"}


def save_settings(settings: Settings) -> None:
    save_json_file(SETTINGS_PATH, settings)


def load_history(max_items: int) -> list[HistoryItem]:
    history = load_json_file(HISTORY_PATH, [])
    if not isinstance(history, list):
        return []
    normalized = []
    for item in history[:max_items]:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "time": str(item.get("time", "")).strip(),
            "action": str(item.get("action", "")).strip(),
            "target": str(item.get("target", "")).strip(),
            "status": str(item.get("status", "info")).strip() or "info",
            "detail": str(item.get("detail", "")).strip(),
        })
    return normalized


def save_history(history_items: list[HistoryItem], max_items: int) -> None:
    save_json_file(HISTORY_PATH, history_items[:max_items])
