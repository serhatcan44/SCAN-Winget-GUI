from __future__ import annotations

from scan_i18n import get_theme_values


def get_ui_texts(lang_texts: dict[str, str]) -> dict[str, str]:
    return {
        "install_button": lang_texts.get("install", "Yükle"),
        "uninstall_button": lang_texts.get("uninstall", "Kaldır"),
        "update_button": lang_texts.get("update", "Güncelle"),
        "helper_tool_button": lang_texts.get("helper_tool", "Yardımcı Araç"),
        "scan_button": lang_texts.get("scan", "Yüklü Uygulamaları Tara"),
        "installed_label": lang_texts.get("installed_apps", "Yüklü Uygulamalar"),
        "not_installed_label": lang_texts.get("not_installed_apps", "Yüklü Olmayan Uygulamalar"),
        "nav_operations": "İşlem Merkezi",
        "nav_history": "Son İşlemler",
        "nav_settings": "Ayarlar",
        "history_refresh": "Yenile",
        "info_title": "Seçili Uygulama",
        "actions_title": "İşlemler",
        "selected_search_placeholder": "Uygulama ara",
        "update_all_button": "Tümünü Güncelle",
        "remove_all_button": lang_texts.get("remove_all", "Tümünü Kaldır"),
    }


def apply_theme_menu_language(theme_menu: object, language: str, current_theme: str) -> None:
