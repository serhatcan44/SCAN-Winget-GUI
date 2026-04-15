from __future__ import annotations

from scan_i18n import get_theme_values


def get_ui_texts(lang_texts: dict[str, str]) -> dict[str, str]:
    return {
        "install_button": lang_texts.get("install", "Yükle"),
        "uninstall_button": lang_texts.get("uninstall", "Kaldır"),
        "update_button": lang_texts.get("update", "Güncelle"),
        "scan_button": lang_texts.get("scan", "Yüklü Uygulamaları Tara"),
        "installed_label": lang_texts.get("installed_apps", "Yüklü Uygulamalar"),
        "not_installed_label": lang_texts.get("not_installed_apps", "Yüklü Olmayan Uygulamalar"),
        "nav_operations": "İşlem Merkezi",
        "nav_history": "Son İşlemler",
        "nav_settings": "Ayarlar",
        "history_refresh": "Yenile",
        "info_title": "Seçili Uygulama",
        "actions_title": "İşlemler",
        "filter_title": "Filtre",
        "search_label": "Ara",
        "search_placeholder": "Uygulama adı veya paket kimliği ile ara",
        "selected_search_placeholder": "Uygulama ara",
        "update_all_button": "Tümünü Güncelle",
        "filter_all": "Tümü",
        "filter_installed": "Kurulu",
        "filter_ready": "Hazır",
    }


def apply_theme_menu_language(theme_menu: object, language: str, current_theme: str) -> None:
    values = get_theme_values(language)
    theme_menu.configure(values=values)
    theme_menu.set(values[0] if current_theme == "Dark" else values[1])


def get_install_status_text(installed: bool) -> str:
    return "Kurulu" if installed else "Kurulu değil"
