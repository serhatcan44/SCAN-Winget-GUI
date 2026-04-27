import os
import re
import sys
import shutil
import subprocess
import threading
import time
import tkinter as tk
import webbrowser
import logging
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
from scan_catalog import APP_ALIASES, APPS
from scan_controllers import (
    bulk_final_status,
    bulk_item_result,
    bulk_precheck,
    helper_missing_feedback,
    helper_result,
    manage_precheck,
    manage_result,
    update_precheck,
    update_result,
)
from scan_i18n import get_theme_values, load_language
from scan_matchers import contains_any_alias, output_contains_any
from scan_operation_logic import (
    CANCEL_TOKENS,
    NOT_INSTALLED_TOKENS,
    NO_UPGRADE_TOKENS,
    build_manage_command,
    build_upgrade_command,
    get_manage_action_meta,
    summarize_bulk_update,
)
from scan_presentation import apply_theme_menu_language, get_install_status_text, get_ui_texts
from scan_services import (
    get_app_aliases as service_get_app_aliases,
    get_bulk_update_candidates as service_get_bulk_update_candidates,
    get_installed_apps_snapshot,
    get_installed_version as service_get_installed_version,
    get_registry_app_details as service_get_registry_app_details,
    get_registry_display_names as service_get_registry_display_names,
    get_winget_package_details as service_get_winget_package_details,
    has_available_upgrade as service_has_available_upgrade,
    is_app_installed as service_is_app_installed,
    is_app_installed_via_winget as service_is_app_installed_via_winget,
    run_helper_executable as service_run_helper_executable,
)
from scan_ui_presenter import (
    apply_operation_feedback as presenter_apply_operation_feedback,
    hide_progress_modal as presenter_hide_progress_modal,
    show_progress_modal as presenter_show_progress_modal,
    update_progress_modal as presenter_update_progress_modal,
)

# Configure logging
log_dir = os.path.join(os.environ["LOCALAPPDATA"], "SCAN")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'scan.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
from scan_storage import load_history, load_settings, save_history, save_settings

try:
    import winreg
except ImportError:
    winreg = None
    logger.warning("winreg modülü yüklenemedi, registry işlemleri devre dışı.")

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT = "Segoe UI"


settings = load_settings()
save_settings(settings)
ctk.set_appearance_mode(settings.get("Theme", "Dark"))


def get_theme_colors(theme_name=None):
    mode = (theme_name or settings.get("Theme", "Dark")).lower()
    if mode == "light":
        return {
            "bg": "#eef4fb",
            "surface": "#ffffff",
            "surface_alt": "#f7faff",
            "surface_soft": "#edf3fb",
            "surface_hover": "#e3edf9",
            "border": "#cfdaea",
            "border_strong": "#b7c6db",
            "text": "#152033",
            "muted": "#5c6b80",
            "accent": "#005cff",
            "accent_hover": "#0047c7",
            "accent_soft": "#d6e4ff",
            "accent_text": "#f8fbff",
            "success": "#00c853",
            "success_hover": "#00a844",
            "success_soft": "#d9ffe8",
            "danger": "#ff1744",
            "danger_hover": "#d5002f",
            "danger_soft": "#ffdce4",
            "button_text": "#ffffff",
            "input_button": "#d9e4f2",
            "input_button_hover": "#cad8ea",
            "overlay": "#d8e2f0",
            "selected_tile": "#d6e4ff",
            "selected_tile_text": "#00318a",
            "badge_installed_bg": "#d6e4ff",
            "badge_installed_text": "#005cff",
            "badge_ready_bg": "#d9ffe8",
            "badge_ready_text": "#00a844",
            "progress_badge_bg": "#d6e4ff",
            "progress_badge_text": "#005cff",
            "signature_text": "#005cff",
            "button_disabled_bg": "#e7edf5",
            "button_disabled_border": "#c7d3e3",
            "button_disabled_text": "#7f8da3",
        }
    return {
        "bg": "#0b1220",
        "surface": "#121a2b",
        "surface_alt": "#182235",
        "surface_soft": "#1b2740",
        "surface_hover": "#223252",
        "border": "#2a3852",
        "border_strong": "#3a4c6a",
        "text": "#e8eef8",
        "muted": "#97a6ba",
        "accent": "#1e90ff",
        "accent_hover": "#0078ff",
        "accent_soft": "#17385b",
        "accent_text": "#f4f8ff",
        "success": "#00e676",
        "success_hover": "#00c853",
        "success_soft": "#173f2c",
        "danger": "#ff1744",
        "danger_hover": "#ff0033",
        "danger_soft": "#4b1f2a",
        "button_text": "#f4f8ff",
        "input_button": "#24344f",
        "input_button_hover": "#2b3f61",
        "overlay": "#0b1220",
        "selected_tile": "#1b3d6d",
        "selected_tile_text": "#f3f8ff",
        "badge_installed_bg": "#17385b",
        "badge_installed_text": "#5eb3ff",
        "badge_ready_bg": "#173f2c",
        "badge_ready_text": "#4dff9a",
        "progress_badge_bg": "#17385b",
        "progress_badge_text": "#5eb3ff",
        "signature_text": "#5eb3ff",
        "button_disabled_bg": "#253246",
        "button_disabled_border": "#34455d",
        "button_disabled_text": "#7f92aa",
    }


THEME = get_theme_colors()
panel_canvases = []
panel_sections = []

DEFAULT_WINDOW_WIDTH = 960
DEFAULT_WINDOW_HEIGHT = 760
MIN_WINDOW_WIDTH = 860
MIN_WINDOW_HEIGHT = 620
WINDOW_MARGIN_X = 80
WINDOW_MARGIN_Y = 120
GITHUB_URL = "https://github.com/serhatcan44"
LINKEDIN_URL = "http://linkedin.com/in/serhat-can"
INSTAGRAM_URL = "https://instagram.com/_canserhat44"

app = ctk.CTk(fg_color=THEME["bg"])
app.title("SCAN")
app.resizable(True, True)

icon_path = resource_path("app_icon.ico")
try:
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)
except Exception as e:
    logger.warning(f"İkon yüklenemedi: {e}")
apps = APPS

icon_cache = {}
scan_lock = threading.Lock()
operation_lock = threading.Lock()
scan_cache = {"timestamp": 0.0, "installed": set()}
registry_cache = {"timestamp": 0.0, "names": []}
operation_state = {"busy": False, "action": None}
search_state = {"query": ""}
selected_action_state = {"install": "disabled", "uninstall": "disabled", "update": "disabled"}
helper_button_state = {"visible": False, "enabled": False}
activate_idm_button_state = {"visible": False, "enabled": False}
history_items = []
current_view = {"name": "operations"}
IDM_APP_NAME = "Internet Download Manager"
IDM_HELPER_BUTTON_TEXT = "IDM Etkinleştir"
IDM_HISTORY_ACTION_NAME = "Etkinleştirme"
settings_nav_state = {"active": "general"}
history_filter_state = {"mode": "all"}
SCAN_CACHE_TTL_SEC = 12
REGISTRY_CACHE_TTL_SEC = 180
MAX_HISTORY_ITEMS = 12
lang_texts = {}
active_scroll_canvas = None
app_tile_widgets = {}
nav_items = {}
history_items = load_history(MAX_HISTORY_ITEMS)
responsive_state = {
    "header_mode": None,
    "actions_mode": None,
    "panel_mode": None,
    "settings_mode": None,
}


def configure_window_bounds():
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    available_width = max(720, screen_width - WINDOW_MARGIN_X)
    available_height = max(540, screen_height - WINDOW_MARGIN_Y)
    window_width = min(DEFAULT_WINDOW_WIDTH, available_width)
    window_height = min(DEFAULT_WINDOW_HEIGHT, available_height)
    min_width = min(MIN_WINDOW_WIDTH, available_width)
    min_height = min(MIN_WINDOW_HEIGHT, available_height)
    pos_x = max((screen_width - window_width) // 2, 0)
    pos_y = max((screen_height - window_height) // 2, 0)

    app.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
    app.minsize(min_width, min_height)


configure_window_bounds()


def apply_theme_colors():
    global THEME
    THEME = get_theme_colors()
    if "app" in globals():
        app.configure(fg_color=THEME["bg"])

    widget_updates = [
        ("shell_frame", {"fg_color": THEME["bg"]}),
        ("hero_frame", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("app_title_label", {"text_color": THEME["text"]}),
        ("hero_subtitle_label", {"text_color": THEME["muted"]}),
        ("theme_menu", {
            "fg_color": THEME["surface_alt"],
            "button_color": THEME["input_button"],
            "button_hover_color": THEME["input_button_hover"],
            "dropdown_fg_color": THEME["surface"],
            "dropdown_hover_color": THEME["surface_hover"],
            "text_color": THEME["text"],
        }),
        ("language_menu", {
            "fg_color": THEME["surface_alt"],
            "button_color": THEME["input_button"],
            "button_hover_color": THEME["input_button_hover"],
            "dropdown_fg_color": THEME["surface"],
            "dropdown_hover_color": THEME["surface_hover"],
            "text_color": THEME["text"],
        }),
        ("github_button", {"fg_color": "transparent", "hover_color": THEME["bg"], "border_color": THEME["bg"]}),
        ("linkedin_button", {"fg_color": "transparent", "hover_color": THEME["bg"], "border_color": THEME["bg"]}),
        ("instagram_button", {"fg_color": "transparent", "hover_color": THEME["bg"], "border_color": THEME["bg"]}),
        ("installed_frame", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("not_installed_frame", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("installed_label", {"text_color": THEME["text"]}),
        ("not_installed_label", {"text_color": THEME["text"]}),
        ("navigation_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("control_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("control_title", {"text_color": THEME["text"]}),
        ("scan_button", {"fg_color": THEME["surface_soft"], "hover_color": THEME["surface_hover"], "text_color": THEME["text"]}),
        ("update_all_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("info_panel", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("info_title", {"text_color": THEME["muted"]}),
        ("selected_search_shell", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("selected_search_entry", {"fg_color": THEME["surface"], "border_color": THEME["surface"], "text_color": THEME["text"]}),
        ("app_list", {
            "fg_color": THEME["surface"],
            "border_color": THEME["border"],
            "button_color": THEME["input_button"],
            "button_hover_color": THEME["input_button_hover"],
            "dropdown_fg_color": THEME["surface"],
            "dropdown_hover_color": THEME["surface_hover"],
            "text_color": THEME["text"],
        }),
        ("selected_app_title", {"text_color": THEME["text"]}),
        ("app_id_label", {"text_color": THEME["muted"]}),
        ("app_id_value", {"text_color": THEME["text"]}),
        ("version_label", {"text_color": THEME["muted"]}),
        ("version_value", {"text_color": THEME["text"]}),
        ("publisher_label", {"text_color": THEME["muted"]}),
        ("publisher_value", {"text_color": THEME["text"]}),
        ("install_status_label", {"text_color": THEME["muted"]}),
        ("install_status_value", {"text_color": THEME["text"]}),
        ("actions_panel", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("actions_title", {"text_color": THEME["muted"]}),
        ("install_button", {"fg_color": THEME["success"], "hover_color": THEME["success_hover"], "text_color": THEME["button_text"]}),
        ("uninstall_button", {"fg_color": THEME["danger"], "hover_color": THEME["danger_hover"], "text_color": THEME["button_text"]}),
        ("update_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "border_color": THEME["accent"], "text_color": THEME["button_text"]}),
        ("helper_button", {"fg_color": THEME["surface_soft"], "hover_color": THEME["surface_hover"], "border_color": THEME["border_strong"], "text_color": THEME["text"]}),
        ("history_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("history_title", {"text_color": THEME["text"]}),
        ("history_subtitle", {"text_color": THEME["muted"]}),
        ("history_clear_button", {"fg_color": THEME["danger"], "hover_color": THEME["danger_hover"], "text_color": THEME["button_text"], "border_color": THEME["danger"]}),
        ("history_refresh_button", {"fg_color": THEME["success"], "hover_color": THEME["success_hover"], "text_color": THEME["button_text"], "border_color": THEME["success"]}),
        ("history_stats_row", {"fg_color": "transparent"}),
        ("history_total_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("history_success_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("history_issue_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("history_total_title", {"text_color": THEME["muted"]}),
        ("history_success_title", {"text_color": THEME["muted"]}),
        ("history_issue_title", {"text_color": THEME["muted"]}),
        ("history_total_value", {"text_color": THEME["text"]}),
        ("history_success_value", {"text_color": THEME["success"]}),
        ("history_issue_value", {"text_color": THEME["danger"]}),
        ("history_feed_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("history_feed_title", {"text_color": THEME["text"]}),
        ("history_feed_hint", {"text_color": THEME["muted"]}),
        ("history_list_frame", {"fg_color": "transparent"}),
        ("settings_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("settings_sidebar", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("settings_sidebar_title", {"text_color": THEME["muted"]}),
        ("appearance_title", {"text_color": THEME["text"]}),
        ("appearance_desc", {"text_color": THEME["muted"]}),
        ("theme_menu", {
            "fg_color": THEME["surface"],
            "button_color": THEME["input_button"],
            "button_hover_color": THEME["input_button_hover"],
            "dropdown_fg_color": THEME["surface"],
            "dropdown_hover_color": THEME["surface_hover"],
            "text_color": THEME["text"],
        }),
        ("language_title", {"text_color": THEME["text"]}),
        ("language_desc", {"text_color": THEME["muted"]}),
        ("activate_windows_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("activate_windows_desc", {"text_color": THEME["muted"]}),
        ("activate_office_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("activate_office_desc", {"text_color": THEME["muted"]}),
        ("activate_idm_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("activate_idm_desc", {"text_color": THEME["muted"]}),
        ("progress_overlay", {"fg_color": THEME["overlay"]}),
        ("progress_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("progress_badge", {"fg_color": THEME["progress_badge_bg"], "text_color": THEME["progress_badge_text"]}),
        ("progress_title_label", {"text_color": THEME["text"]}),
        ("progress_detail_label", {"text_color": THEME["muted"]}),
        ("progress_modal_bar", {"progress_color": THEME["accent"], "fg_color": THEME["border"]}),
        ("progress_hint_label", {"text_color": THEME["muted"]}),
    ]

    for widget_name, options in widget_updates:
        widget = globals().get(widget_name)
        if widget is not None:
            widget.configure(**options)

    for canvas in panel_canvases:
        try:
            canvas.configure(bg=THEME["surface"])
        except Exception as e:
            logger.warning(f"Canvas güncellenemedi: {e}")

    if "signature_canvas" in globals():
        try:
            signature_canvas.configure(bg=THEME["bg"], highlightbackground=THEME["bg"])
            if "signature_text_item" in globals():
                signature_canvas.itemconfigure(signature_text_item, fill=THEME["signature_text"])
        except Exception as e:
            logger.warning(f"İmza alanı güncellenemedi: {e}")

    if "settings_nav_general" in globals():
        update_settings_nav_styles()

    if "selected_search_icon" in globals():
        draw_search_icon(selected_search_icon)

    for section in panel_sections:
        section["panel"].configure(fg_color=THEME["surface"], border_color=THEME["border"])
        section["title"].configure(text_color=THEME["text"])
        section["desc"].configure(text_color=THEME["muted"])
        section["body"].configure(fg_color=THEME["surface"])
        section["content"].configure(fg_color=THEME["surface"])

    update_selected_app_highlight()
    update_helper_button_text()
    update_navigation_styles()
    update_helper_button_visibility()
    update_history_filter_cards()
    render_history_view()


def on_global_mousewheel(event):
    if active_scroll_canvas is None:
        return
    try:
        delta = event.delta
        if delta == 0:
            return "break"
        scroll_units = -1 if delta > 0 else 1
        active_scroll_canvas.yview_scroll(scroll_units, "units")
    except Exception as e:
        logger.warning(f"Mouse wheel scroll hatası: {e}")
    return "break"


app.bind_all("<MouseWheel>", on_global_mousewheel)


def build_icon(app_name, size):
    cache_key = (app_name, size)
    if cache_key not in icon_cache:
        logo_path = resource_path(os.path.join("icons", apps[app_name]["logo"]))
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((size, size), Image.LANCZOS)
            icon_cache[cache_key] = CTkImage(light_image=img, dark_image=img, size=(size, size))
    return icon_cache.get(cache_key)


def build_ui_icon(filename, size):
    cache_key = (filename, size)
    if cache_key not in icon_cache:
        icon_path = resource_path(os.path.join("icons", filename))
        if os.path.exists(icon_path):
            img = Image.open(icon_path).resize((size, size), Image.LANCZOS)
            icon_cache[cache_key] = CTkImage(light_image=img, dark_image=img, size=(size, size))
    return icon_cache.get(cache_key)


def create_panel(parent, title_text, description_text):
    global active_scroll_canvas

    panel = ctk.CTkFrame(parent, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
    header = ctk.CTkFrame(panel, fg_color="transparent")
    header.pack(fill="x", padx=14, pady=(14, 8))
    title = ctk.CTkLabel(header, text=title_text, font=(FONT, 15, "bold"), text_color=THEME["text"])
    title.pack(anchor="w", pady=(0, 2))
    desc = ctk.CTkLabel(header, text=description_text, font=(FONT, 10), text_color=THEME["muted"])
    desc.pack(anchor="w")
    body = ctk.CTkFrame(panel, fg_color=THEME["surface"])
    body.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    canvas = tk.Canvas(body, bg=THEME["surface"], highlightthickness=0, bd=0, relief="flat")
    canvas.pack(fill="both", expand=True)

    content = ctk.CTkFrame(canvas, fg_color=THEME["surface"])
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def sync_scrollregion(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def sync_width(event):
        canvas.itemconfigure(canvas_window, width=event.width)

    def activate_scroll(_event):
        global active_scroll_canvas
        active_scroll_canvas = canvas

    def deactivate_scroll(_event):
        global active_scroll_canvas
        if active_scroll_canvas == canvas:
            active_scroll_canvas = None

    content.bind("<Configure>", sync_scrollregion)
    canvas.bind("<Configure>", sync_width)
    canvas.bind("<Enter>", activate_scroll)
    canvas.bind("<Leave>", deactivate_scroll)
    content.bind("<Enter>", activate_scroll)
    content.bind("<Leave>", deactivate_scroll)
    content._scroll_canvas = canvas
    panel_canvases.append(canvas)
    panel_sections.append({
        "panel": panel,
        "title": title,
        "desc": desc,
        "body": body,
        "content": content,
    })

    return panel, title, content


def draw_search_icon(canvas):
    if canvas is None:
        return
    canvas.delete("all")
    icon_color = THEME["muted"]
    canvas.configure(bg=THEME["surface"])
    canvas.create_oval(4, 4, 12, 12, outline=icon_color, width=1.6)
    canvas.create_line(11, 11, 15, 15, fill=icon_color, width=1.6)


def handle_app_click(event):
    widget = event.widget
    if "selected_search_entry" not in globals():
        return
    widget_path = str(widget)
    search_widgets = {
        str(selected_search_entry),
        str(selected_search_shell),
        str(selected_search_icon),
    }
    if widget_path in search_widgets or widget_path.startswith(f"{selected_search_entry}.") or widget_path.startswith(f"{selected_search_shell}."):
        app.after(0, lambda: selected_search_entry.focus_set())
        return
    if selected_search_entry.focus_get() == selected_search_entry:
        app.after(0, close_search_focus)


def close_search_focus():
    if "selected_search_entry" not in globals():
        return
    try:
        selected_search_entry.selection_clear()
    except Exception:
        pass
    try:
        selected_search_entry.icursor(0)
    except Exception:
        pass
    app.focus_set()
    focus_sink.focus_force()


shell_frame = ctk.CTkFrame(app, fg_color=THEME["bg"])
shell_frame.pack(fill="both", expand=True, padx=14, pady=14)
focus_sink = tk.Entry(shell_frame, width=1, highlightthickness=0, bd=0, relief="flat", bg=THEME["bg"], fg=THEME["bg"], insertbackground=THEME["bg"])
focus_sink.place(x=-100, y=-100, width=1, height=1)
app.bind_all("<Button-1>", handle_app_click, add="+")
hero_frame = ctk.CTkFrame(shell_frame, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
hero_text_frame = ctk.CTkFrame(hero_frame, fg_color="transparent")
hero_text_frame.pack(side="left", fill="both", expand=True, padx=16, pady=14)
app_title_label = ctk.CTkLabel(hero_text_frame, text="SCAN", font=(FONT, 20, "bold"), text_color=THEME["text"])
app_title_label.pack(anchor="w")
hero_subtitle_label = ctk.CTkLabel(hero_text_frame, text="Windows uygulamalarını temiz bir panelden tarayın ve yönetin.", font=(FONT, 10), text_color=THEME["muted"])
hero_subtitle_label.pack(anchor="w", pady=(4, 0))
top_frame = ctk.CTkFrame(hero_frame, fg_color="transparent")


def change_theme(theme):
    dark_variants = {"Koyu", "Dark", "Тёмная", "Dunkel", "深色", "Oscuro", "داكن"}
    light_variants = {"Açık", "Light", "Светлая", "Hell", "浅色", "Claro", "فاتح"}
    if theme in dark_variants:
        ctk.set_appearance_mode("dark")
        settings["Theme"] = "Dark"
    elif theme in light_variants:
        ctk.set_appearance_mode("light")
        settings["Theme"] = "Light"
    save_settings(settings)
    apply_theme_colors()


def apply_language_theme_choices(language):
    apply_theme_menu_language(theme_menu, language, settings["Theme"])


def open_external_link(url):
    try:
        webbrowser.open_new_tab(url)
    except Exception as e:
        logger.warning(f"Bağlantı açılamadı: {e}")


def update_helper_button_text():
    if "helper_button" not in globals():
        return
    default_text = get_ui_texts(lang_texts).get("helper_tool_button", "Yardımcı Araç")
    selected_app = app_list.get() if "app_list" in globals() else ""
    helper_button.configure(text=IDM_HELPER_BUTTON_TEXT if selected_app == IDM_APP_NAME else default_text)


def set_settings_nav(section_key):
    settings_nav_state["active"] = section_key
    update_settings_nav_styles()
    update_settings_content()
    if section_key == "general":
        app.after(0, lambda: theme_menu.focus_set())


def update_settings_nav_styles():
    nav_widgets = {
        "general": globals().get("settings_nav_general"),
        "activate": globals().get("settings_nav_activate"),
    }
    for key, widget in nav_widgets.items():
        if widget is None:
            continue
        is_active = settings_nav_state["active"] == key
        widget.configure(
            fg_color=THEME["accent_soft"] if is_active else "transparent",
            hover_color=THEME["surface_hover"],
            text_color=THEME["accent"] if is_active else THEME["text"],
        )


def update_settings_content():
    content_sections = {
        "general": globals().get("settings_general_content"),
        "activate": globals().get("settings_activate_content"),
    }
    for key, section in content_sections.items():
        if section is None:
            continue
        if key == settings_nav_state["active"]:
            section.pack(fill="both", expand=True)
        else:
            section.pack_forget()


navigation_card = ctk.CTkFrame(shell_frame, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
navigation_card.pack(fill="x", pady=(0, 10))
navigation_inner = ctk.CTkFrame(navigation_card, fg_color="transparent")
navigation_inner.pack(fill="x", padx=12, pady=10)
navigation_tabs = ctk.CTkFrame(navigation_inner, fg_color="transparent")
navigation_tabs.pack(anchor="center")


def create_navigation_item(parent, label, key):
    item = ctk.CTkFrame(parent, fg_color="transparent")
    item.pack(side="left", padx=(0, 14))
    button = ctk.CTkButton(
        item,
        text=label,
        command=lambda selected=key: switch_view(selected),
        width=160,
        height=36,
        corner_radius=12,
        fg_color="transparent",
        hover_color=THEME["surface_hover"],
        text_color=THEME["muted"],
        font=(FONT, 12, "bold"),
    )
    button.pack()
    underline = ctk.CTkFrame(item, fg_color=THEME["surface"], height=3, corner_radius=2)
    underline.pack(fill="x", padx=18, pady=(6, 0))
    nav_items[key] = {"button": button, "underline": underline}


create_navigation_item(navigation_tabs, "İşlem Merkezi", "operations")
create_navigation_item(navigation_tabs, "Son İşlemler", "history")
create_navigation_item(navigation_tabs, "Ayarlar", "settings")

content_host = ctk.CTkFrame(shell_frame, fg_color="transparent")
content_host.pack(fill="both", expand=True)
content_views = {}

operations_view = ctk.CTkFrame(content_host, fg_color="transparent")
history_view = ctk.CTkFrame(content_host, fg_color="transparent")
settings_view = ctk.CTkFrame(content_host, fg_color="transparent")
content_views["operations"] = operations_view
content_views["history"] = history_view
content_views["settings"] = settings_view

control_card = ctk.CTkFrame(operations_view, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
control_card.pack(fill="x", pady=(0, 10))
control_inner = ctk.CTkFrame(control_card, fg_color="transparent")
control_inner.pack(fill="x", padx=14, pady=12)
control_header = ctk.CTkFrame(control_inner, fg_color="transparent")
control_header.pack(fill="x")
control_title = ctk.CTkLabel(control_header, text="İşlem Merkezi", font=(FONT, 15, "bold"), text_color=THEME["text"])
control_title.pack(side="left")

control_actions = ctk.CTkFrame(control_header, fg_color="transparent")
control_actions.pack(side="right")
update_all_button = ctk.CTkButton(control_actions, text="Tümünü Güncelle", width=140, height=32, corner_radius=10, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"))
update_all_button.pack(side="left", padx=(0, 8))
scan_button = ctk.CTkButton(control_actions, text="Tara", width=90, height=32, corner_radius=10, fg_color=THEME["surface_soft"], hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
scan_button.pack(side="left")

action_row = ctk.CTkFrame(control_inner, fg_color="transparent")
action_row.pack(fill="x", pady=(10, 0))

info_panel = ctk.CTkFrame(action_row, fg_color=THEME["surface_alt"], corner_radius=12, border_width=1, border_color=THEME["border"])
info_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
info_header = ctk.CTkFrame(info_panel, fg_color="transparent")
info_header.pack(fill="x", padx=12, pady=(10, 8))
info_title = ctk.CTkLabel(info_header, text="Seçili Uygulama", font=(FONT, 11, "bold"), text_color=THEME["muted"])
info_title.pack(anchor="w")
selector_row = ctk.CTkFrame(info_header, fg_color="transparent")
selector_row.pack(fill="x", pady=(8, 0))
app_list = ctk.CTkComboBox(selector_row, values=list(apps.keys()), width=220, height=34, corner_radius=10, border_width=1, fg_color=THEME["surface"], border_color=THEME["border"], button_color=THEME["input_button"], button_hover_color=THEME["input_button_hover"], dropdown_fg_color=THEME["surface"], dropdown_hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
app_list.pack(side="left")
app_list.set("Google Chrome")
selected_search_shell = ctk.CTkFrame(selector_row, fg_color=THEME["surface"], corner_radius=10, border_width=1, border_color=THEME["border"], height=34)
selected_search_shell.pack(side="left", fill="x", expand=True, padx=(10, 0))
selected_search_shell.pack_propagate(False)
selected_search_icon = tk.Canvas(selected_search_shell, width=18, height=18, highlightthickness=0, bd=0, relief="flat")
selected_search_icon.pack(side="left", padx=(12, 4), pady=7)
draw_search_icon(selected_search_icon)
selected_search_entry = ctk.CTkEntry(selected_search_shell, placeholder_text="Uygulama ara", height=30, corner_radius=0, border_width=0, fg_color=THEME["surface"], border_color=THEME["surface"], text_color=THEME["text"])
selected_search_entry.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=2)
selected_search_entry.bind("<KeyRelease>", lambda _event: set_search_query(selected_search_entry.get(), source="selected"))
selected_search_entry.bind("<Escape>", lambda _event: close_search_focus())
selected_search_entry.bind("<FocusOut>", lambda _event: app.after(0, lambda: selected_search_entry.selection_clear()))
selected_search_shell.bind("<Button-1>", lambda _event: selected_search_entry.focus_set())
selected_search_icon.bind("<Button-1>", lambda _event: selected_search_entry.focus_set())

selected_summary = ctk.CTkFrame(info_panel, fg_color="transparent")
selected_summary.pack(fill="x", padx=12, pady=(2, 10))
selected_logo_label = ctk.CTkLabel(selected_summary, text="", width=52, height=52)
selected_logo_label.pack(side="left", padx=(0, 10))
selected_texts = ctk.CTkFrame(selected_summary, fg_color="transparent")
selected_texts.pack(side="left", fill="both", expand=True)
selected_app_title = ctk.CTkLabel(selected_texts, text="Google Chrome", font=(FONT, 15, "bold"), text_color=THEME["text"])
selected_app_title.pack(anchor="w")

details_grid = ctk.CTkFrame(selected_texts, fg_color="transparent")
details_grid.pack(fill="x", pady=(6, 0))
details_grid.grid_columnconfigure(0, weight=0)
details_grid.grid_columnconfigure(1, weight=1)
details_grid.grid_columnconfigure(2, weight=0)
details_grid.grid_columnconfigure(3, weight=1)
app_id_label = ctk.CTkLabel(details_grid, text="Paket", font=(FONT, 10), text_color=THEME["muted"])
app_id_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
app_id_value = ctk.CTkLabel(details_grid, text="", font=(FONT, 10, "bold"), text_color=THEME["text"], anchor="w")
app_id_value.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=2)
version_label = ctk.CTkLabel(details_grid, text="Sürüm", font=(FONT, 10), text_color=THEME["muted"])
version_label.grid(row=0, column=2, sticky="w", padx=(0, 8), pady=2)
version_value = ctk.CTkLabel(details_grid, text="", font=(FONT, 10, "bold"), text_color=THEME["text"], anchor="w")
version_value.grid(row=0, column=3, sticky="w", pady=2)
publisher_label = ctk.CTkLabel(details_grid, text="Yapımcı", font=(FONT, 10), text_color=THEME["muted"])
publisher_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
publisher_value = ctk.CTkLabel(details_grid, text="", font=(FONT, 10, "bold"), text_color=THEME["text"], anchor="w")
publisher_value.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=2)
install_status_label = ctk.CTkLabel(details_grid, text="Durum", font=(FONT, 10), text_color=THEME["muted"])
install_status_label.grid(row=1, column=2, sticky="w", padx=(0, 8), pady=2)
install_status_value = ctk.CTkLabel(details_grid, text="", font=(FONT, 10, "bold"), text_color=THEME["text"], anchor="w")
install_status_value.grid(row=1, column=3, sticky="w", pady=2)

actions_panel = ctk.CTkFrame(action_row, fg_color=THEME["surface_alt"], corner_radius=12, border_width=1, border_color=THEME["border"], width=156, height=208)
actions_panel.pack(side="left", fill="y", padx=(8, 0))
actions_panel.pack_propagate(False)
actions_title = ctk.CTkLabel(actions_panel, text="İşlemler", font=(FONT, 11, "bold"), text_color=THEME["muted"])
actions_title.pack(anchor="w", padx=12, pady=(10, 6))
install_button = ctk.CTkButton(actions_panel, text="Yükle", width=128, height=30, corner_radius=9, fg_color=THEME["success"], hover_color=THEME["success_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: manage_app("install"))
install_button.pack(anchor="w", padx=12, pady=(0, 6))
uninstall_button = ctk.CTkButton(actions_panel, text="Kaldır", width=128, height=30, corner_radius=9, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: manage_app("uninstall"))
uninstall_button.pack(anchor="w", padx=12, pady=(0, 6))
update_button = ctk.CTkButton(actions_panel, text="Güncelle", width=128, height=30, corner_radius=9, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], border_width=1, border_color=THEME["accent"], text_color=THEME["button_text"], font=(FONT, 11, "bold"))
update_button.pack(anchor="w", padx=12, pady=(0, 6))
helper_button = ctk.CTkButton(actions_panel, text="Yardımcı Araç", width=128, height=30, corner_radius=9, border_width=1, fg_color=THEME["surface_soft"], hover_color=THEME["surface_hover"], border_color=THEME["border_strong"], text_color=THEME["text"], font=(FONT, 11, "bold"))

main_frame = ctk.CTkFrame(operations_view, fg_color="transparent")
main_frame.pack(fill="both", expand=True)
panel_row = ctk.CTkFrame(main_frame, fg_color="transparent")
panel_row.pack(fill="both", expand=True)
installed_frame, installed_label, installed_icons_frame = create_panel(panel_row, "Yüklü Uygulamalar", "Sisteminizde bulunan uygulamalar burada görünür.")
installed_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
not_installed_frame, not_installed_label, not_installed_icons_frame = create_panel(panel_row, "Yüklü Olmayan Uygulamalar", "Kurulabilir uygulamaları bu panelden takip edebilirsiniz.")
not_installed_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

history_card = ctk.CTkFrame(history_view, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_card.pack(fill="both", expand=True)
history_inner = ctk.CTkFrame(history_card, fg_color="transparent")
history_inner.pack(fill="both", expand=True, padx=14, pady=14)
history_header = ctk.CTkFrame(history_inner, fg_color="transparent")
history_header.pack(fill="x")
history_title = ctk.CTkLabel(history_header, text="Son İşlemler", font=(FONT, 16, "bold"), text_color=THEME["text"])
history_title.pack(side="left")
history_actions = ctk.CTkFrame(history_header, fg_color="transparent")
history_actions.pack(side="right")
history_clear_button = ctk.CTkButton(history_actions, text="Temizle", width=96, height=32, corner_radius=10, border_width=1, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], border_color=THEME["danger"], text_color=THEME["button_text"], font=(FONT, 10, "bold"))
history_clear_button.pack(side="left", padx=(0, 8))
history_refresh_button = ctk.CTkButton(history_actions, text="Yenile", width=96, height=32, corner_radius=10, border_width=1, fg_color=THEME["success"], hover_color=THEME["success_hover"], border_color=THEME["success"], text_color=THEME["button_text"], font=(FONT, 10, "bold"))
history_refresh_button.pack(side="right")
history_subtitle = ctk.CTkLabel(history_inner, text="Son yükleme, kaldırma ve güncelleme sonuçlarını zaman bilgisiyle burada takip edebilirsiniz.", font=(FONT, 10), text_color=THEME["muted"])
history_subtitle.pack(anchor="w", pady=(8, 12))
history_stats_row = ctk.CTkFrame(history_inner, fg_color="transparent")
history_stats_row.pack(fill="x", pady=(0, 12))

history_total_card = ctk.CTkFrame(history_stats_row, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_total_card.pack(side="left", fill="x", expand=True, padx=(0, 8))
history_total_inner = ctk.CTkFrame(history_total_card, fg_color="transparent")
history_total_inner.pack(fill="both", expand=True, padx=14, pady=12)
history_total_title = ctk.CTkLabel(history_total_inner, text="Toplam Kayıt", font=(FONT, 10), text_color=THEME["muted"])
history_total_title.pack(anchor="w")
history_total_value = ctk.CTkLabel(history_total_inner, text="0", font=(FONT, 18, "bold"), text_color=THEME["text"])
history_total_value.pack(anchor="w", pady=(4, 0))

history_success_card = ctk.CTkFrame(history_stats_row, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_success_card.pack(side="left", fill="x", expand=True, padx=8)
history_success_inner = ctk.CTkFrame(history_success_card, fg_color="transparent")
history_success_inner.pack(fill="both", expand=True, padx=14, pady=12)
history_success_title = ctk.CTkLabel(history_success_inner, text="Başarılı", font=(FONT, 10), text_color=THEME["muted"])
history_success_title.pack(anchor="w")
history_success_value = ctk.CTkLabel(history_success_inner, text="0", font=(FONT, 18, "bold"), text_color=THEME["success"])
history_success_value.pack(anchor="w", pady=(4, 0))

history_issue_card = ctk.CTkFrame(history_stats_row, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_issue_card.pack(side="left", fill="x", expand=True, padx=(8, 0))
history_issue_inner = ctk.CTkFrame(history_issue_card, fg_color="transparent")
history_issue_inner.pack(fill="both", expand=True, padx=14, pady=12)
history_issue_title = ctk.CTkLabel(history_issue_inner, text="Uyarı / Hata", font=(FONT, 10), text_color=THEME["muted"])
history_issue_title.pack(anchor="w")
history_issue_value = ctk.CTkLabel(history_issue_inner, text="0", font=(FONT, 18, "bold"), text_color=THEME["danger"])
history_issue_value.pack(anchor="w", pady=(4, 0))

for widget in [history_total_card, history_total_inner, history_total_title, history_total_value]:
    widget.bind("<Button-1>", lambda _event: set_history_filter("all"))

for widget in [history_success_card, history_success_inner, history_success_title, history_success_value]:
    widget.bind("<Button-1>", lambda _event: set_history_filter("success"))

for widget in [history_issue_card, history_issue_inner, history_issue_title, history_issue_value]:
    widget.bind("<Button-1>", lambda _event: set_history_filter("issues"))

history_feed_card = ctk.CTkFrame(history_inner, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_feed_card.pack(fill="both", expand=True)
history_feed_inner = ctk.CTkFrame(history_feed_card, fg_color="transparent")
history_feed_inner.pack(fill="both", expand=True, padx=14, pady=14)
history_feed_header = ctk.CTkFrame(history_feed_inner, fg_color="transparent")
history_feed_header.pack(fill="x")
history_feed_title = ctk.CTkLabel(history_feed_header, text="Kayıt Akışı", font=(FONT, 12, "bold"), text_color=THEME["text"])
history_feed_title.pack(side="left")
history_feed_hint = ctk.CTkLabel(history_feed_header, text="En yeni işlemler üstte görünür.", font=(FONT, 10), text_color=THEME["muted"])
history_feed_hint.pack(side="right")

# Scroll canvas oluştur (gizli scrollbar)
history_feed_canvas = tk.Canvas(history_feed_inner, bg=THEME["surface_alt"], highlightthickness=0, bd=0, relief="flat", height=280)
history_feed_canvas.pack(fill="both", expand=True, pady=(10, 0))

history_list_frame = ctk.CTkFrame(history_feed_canvas, fg_color=THEME["surface_alt"])
canvas_window = history_feed_canvas.create_window((0, 0), window=history_list_frame, anchor="nw")

def sync_history_scroll_region(_event=None):
    def update_scroll():
        try:
            bbox = history_feed_canvas.bbox("all")
            if bbox:
                history_feed_canvas.configure(scrollregion=bbox)
        except Exception as e:
            logger.warning(f"History scroll region güncellenemedi: {e}")
    
    # Birkaç kez dene, bazen ilk seferde bbox hazır olmayabilir
    app.after(10, update_scroll)
    app.after(50, update_scroll)
    app.after(100, update_scroll)

def sync_history_width(event):
    canvas_width = event.width
    history_feed_canvas.itemconfig(canvas_window, width=canvas_width)

def activate_history_scroll(_event):
    global active_scroll_canvas
    active_scroll_canvas = history_feed_canvas

def deactivate_history_scroll(_event):
    global active_scroll_canvas
    if active_scroll_canvas == history_feed_canvas:
        active_scroll_canvas = None

history_list_frame.bind("<Configure>", sync_history_scroll_region)
history_feed_canvas.bind("<Configure>", sync_history_width)
history_feed_canvas.bind("<Enter>", activate_history_scroll)
history_feed_canvas.bind("<Leave>", deactivate_history_scroll)
history_list_frame.bind("<Enter>", activate_history_scroll)
history_list_frame.bind("<Leave>", deactivate_history_scroll)

settings_card = ctk.CTkFrame(settings_view, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
settings_card.pack(fill="both", expand=True)
settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
settings_inner.pack(fill="both", expand=True, padx=14, pady=14)
settings_layout = ctk.CTkFrame(settings_inner, fg_color="transparent")
settings_layout.pack(fill="both", expand=True)
settings_sidebar = ctk.CTkFrame(settings_layout, fg_color=THEME["surface_alt"], corner_radius=16, border_width=1, border_color=THEME["border"], width=240)
settings_sidebar.pack(side="left", fill="y", padx=(0, 18))
settings_sidebar.pack_propagate(False)
settings_sidebar_inner = ctk.CTkFrame(settings_sidebar, fg_color="transparent")
settings_sidebar_inner.pack(fill="both", expand=True, padx=16, pady=16)
settings_sidebar_title = ctk.CTkLabel(settings_sidebar_inner, text="MENÜ", font=(FONT, 10, "bold"), text_color=THEME["muted"])
settings_sidebar_title.pack(anchor="w", pady=(0, 12))
settings_nav_general = ctk.CTkButton(settings_sidebar_inner, text="Genel", height=40, corner_radius=12, fg_color=THEME["accent_soft"], hover_color=THEME["surface_hover"], text_color=THEME["accent"], anchor="w", font=(FONT, 13, "bold"), command=lambda: set_settings_nav("general"))
settings_nav_general.pack(fill="x", pady=(0, 8))
settings_nav_activate = ctk.CTkButton(settings_sidebar_inner, text="Activate", height=36, corner_radius=10, fg_color="transparent", hover_color=THEME["surface_hover"], text_color=THEME["text"], anchor="w", font=(FONT, 12, "bold"), command=lambda: set_settings_nav("activate"))
settings_nav_activate.pack(fill="x")

settings_content = ctk.CTkFrame(settings_layout, fg_color="transparent")
settings_content.pack(side="left", fill="both", expand=True)

settings_general_content = ctk.CTkFrame(settings_content, fg_color="transparent")
settings_general_content.pack(fill="both", expand=True)
appearance_row = ctk.CTkFrame(settings_general_content, fg_color="transparent")
appearance_row.pack(fill="x", pady=(8, 12))
appearance_meta = ctk.CTkFrame(appearance_row, fg_color="transparent")
appearance_meta.pack(side="left", fill="x", expand=True)
appearance_title = ctk.CTkLabel(appearance_meta, text="Tema Modu", font=(FONT, 14, "bold"), text_color=THEME["text"])
appearance_title.pack(anchor="w")
appearance_desc = ctk.CTkLabel(appearance_meta, text="Açık veya koyu tema seçin.", font=(FONT, 11), text_color=THEME["muted"], justify="left")
appearance_desc.pack(anchor="w", pady=(4, 0))
theme_menu = ctk.CTkOptionMenu(appearance_row, values=["Dark", "Light"], command=change_theme, width=190, height=38, fg_color=THEME["surface"], button_color=THEME["input_button"], button_hover_color=THEME["input_button_hover"], dropdown_fg_color=THEME["surface"], dropdown_hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
theme_menu.pack(side="right")

language_row = ctk.CTkFrame(settings_general_content, fg_color="transparent")
language_row.pack(fill="x", pady=(0, 6))
language_meta = ctk.CTkFrame(language_row, fg_color="transparent")
language_meta.pack(side="left", fill="x", expand=True)
language_title = ctk.CTkLabel(language_meta, text="Dil", font=(FONT, 14, "bold"), text_color=THEME["text"])
language_title.pack(anchor="w")
language_desc = ctk.CTkLabel(language_meta, text="Uygulama dilini seçin.", font=(FONT, 11), text_color=THEME["muted"], justify="left")
language_desc.pack(anchor="w", pady=(4, 0))
language_menu = ctk.CTkOptionMenu(language_row, values=["Türkçe", "English", "Русский", "Deutsch", "中文", "Español", "العربية"], command=lambda language: change_language(language), width=190, height=38, fg_color=THEME["surface"], button_color=THEME["input_button"], button_hover_color=THEME["input_button_hover"], dropdown_fg_color=THEME["surface"], dropdown_hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
language_menu.pack(side="right")

settings_activate_content = ctk.CTkFrame(settings_content, fg_color="transparent")
activate_windows_row = ctk.CTkFrame(settings_activate_content, fg_color="transparent")
activate_windows_row.pack(fill="x", pady=(8, 12))
activate_windows_meta = ctk.CTkFrame(activate_windows_row, fg_color="transparent")
activate_windows_meta.pack(side="left", fill="x", expand=True)
activate_windows_button = ctk.CTkButton(activate_windows_row, text="Windows", width=190, height=38, corner_radius=10, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: None)
activate_windows_button.pack(side="right")
activate_windows_desc = ctk.CTkLabel(activate_windows_meta, text="Windows Etkinleştirme", font=(FONT, 15, "bold"), text_color=THEME["text"], justify="left")
activate_windows_desc.pack(anchor="w", pady=(7, 0))

activate_office_row = ctk.CTkFrame(settings_activate_content, fg_color="transparent")
activate_office_row.pack(fill="x", pady=(0, 12))
activate_office_meta = ctk.CTkFrame(activate_office_row, fg_color="transparent")
activate_office_meta.pack(side="left", fill="x", expand=True)
activate_office_button = ctk.CTkButton(activate_office_row, text="Office", width=190, height=38, corner_radius=10, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: None)
activate_office_button.pack(side="right")
activate_office_desc = ctk.CTkLabel(activate_office_meta, text="Office Etkinleştirme", font=(FONT, 15, "bold"), text_color=THEME["text"], justify="left")
activate_office_desc.pack(anchor="w", pady=(7, 0))

activate_idm_row = ctk.CTkFrame(settings_activate_content, fg_color="transparent")
activate_idm_row.pack(fill="x")
activate_idm_meta = ctk.CTkFrame(activate_idm_row, fg_color="transparent")
activate_idm_meta.pack(side="left", fill="x", expand=True)
activate_idm_button = ctk.CTkButton(activate_idm_row, text="IDM", width=190, height=38, corner_radius=10, fg_color=THEME["accent"], hover_color=THEME["accent_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"))
activate_idm_button.pack(side="right")
activate_idm_desc = ctk.CTkLabel(activate_idm_meta, text="IDM Etkinleştirme", font=(FONT, 15, "bold"), text_color=THEME["text"], justify="left")
activate_idm_desc.pack(anchor="w", pady=(7, 0))


def apply_responsive_layout(width=None):
    if width is None or width <= 1:
        width = app.winfo_width()

    header_mode = "stacked" if width < 1020 else "wide"
    actions_mode = "stacked" if width < 980 else "wide"
    panel_mode = "stacked" if width < 1180 else "wide"
    settings_mode = "stacked" if width < 980 else "wide"

    if responsive_state["header_mode"] != header_mode:
        control_title.pack_forget()
        control_actions.pack_forget()
        if header_mode == "stacked":
            control_title.pack(anchor="w")
            control_actions.pack(anchor="w", pady=(10, 0))
        else:
            control_title.pack(side="left")
            control_actions.pack(side="right")
        responsive_state["header_mode"] = header_mode

    if responsive_state["actions_mode"] != actions_mode:
        info_panel.pack_forget()
        actions_panel.pack_forget()
        if actions_mode == "stacked":
            actions_panel.configure(width=0, height=152)
            info_panel.pack(fill="both", expand=True, pady=(0, 8))
            actions_panel.pack(fill="x")
        else:
            actions_panel.configure(width=156, height=208)
            info_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
            actions_panel.pack(side="left", fill="y", padx=(8, 0))
        responsive_state["actions_mode"] = actions_mode

    if responsive_state["panel_mode"] != panel_mode:
        installed_frame.pack_forget()
        not_installed_frame.pack_forget()
        if panel_mode == "stacked":
            installed_frame.pack(fill="both", expand=True, pady=(0, 8))
            not_installed_frame.pack(fill="both", expand=True, pady=(8, 0))
        else:
            installed_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
            not_installed_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))
        responsive_state["panel_mode"] = panel_mode

    if responsive_state["settings_mode"] != settings_mode:
        settings_sidebar.pack_forget()
        settings_content.pack_forget()
        if settings_mode == "stacked":
            settings_sidebar.configure(width=0, height=104)
            settings_sidebar.pack(fill="x", pady=(0, 12))
            settings_content.pack(fill="both", expand=True)
        else:
            settings_sidebar.configure(width=240, height=0)
            settings_sidebar.pack(side="left", fill="y", padx=(0, 18))
            settings_content.pack(side="left", fill="both", expand=True)
        responsive_state["settings_mode"] = settings_mode


def handle_window_resize(event):
    if event.widget is app:
        apply_responsive_layout(event.width)


def select_app(app_name: str) -> None:
    if app_name not in apps:
        return
    app_list.set(app_name)
    refresh_selected_app_details()
    update_selected_app_highlight()


def update_selected_app_highlight() -> None:
    selected_name = app_list.get() if "app_list" in globals() else ""
    for app_name, widgets in app_tile_widgets.items():
        is_selected = app_name == selected_name
        widgets["tile"].configure(
            fg_color=THEME["selected_tile"] if is_selected else THEME["surface_soft"],
            border_color=THEME["accent"] if is_selected else THEME["border"],
        )
        widgets["name_label"].configure(text_color=THEME["selected_tile_text"] if is_selected else THEME["text"])


def add_icons(app_list, container):
    max_columns = 4
    total_icons = len(app_list)
    icon_size = 56 if total_icons <= 12 else 48
    selected_name = globals().get("app_list").get() if "app_list" in globals() else ""
    scroll_canvas = getattr(container, "_scroll_canvas", None)

    def activate_scroll_target(_event, canvas=scroll_canvas):
        global active_scroll_canvas
        active_scroll_canvas = canvas

    for column in range(max_columns):
        container.grid_columnconfigure(column, weight=1)
    row = 0
    col = 0
    for app_name in app_list:
        if app_name not in apps:
            continue
        icon = build_icon(app_name, icon_size)
        if icon is None:
            continue
        is_selected = app_name == selected_name
        tile = ctk.CTkFrame(
            container,
            fg_color=THEME["selected_tile"] if is_selected else THEME["surface_soft"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["accent"] if is_selected else THEME["border"],
        )
        tile.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        icon_label = ctk.CTkLabel(tile, image=icon, text="")
        icon_label.pack(padx=10, pady=(10, 6))
        name_label = ctk.CTkLabel(tile, text=app_name, font=(FONT, 10, "bold"), text_color=THEME["text"], wraplength=92, justify="center")
        name_label.pack(padx=6, pady=(0, 10))

        for widget in (tile, icon_label, name_label):
            widget.bind("<Button-1>", lambda _event, selected=app_name: select_app(selected))
            widget.bind("<Enter>", activate_scroll_target)

        app_tile_widgets[app_name] = {"tile": tile, "name_label": name_label}
        col += 1
        if col >= max_columns:
            col = 0
            row += 1


def render_installed_apps(installed_apps: set[str]) -> None:
    app_tile_widgets.clear()
    for widget in installed_icons_frame.winfo_children():
        widget.destroy()
    for widget in not_installed_icons_frame.winfo_children():
        widget.destroy()
    installed_sorted = sorted(app_name for app_name in installed_apps if matches_search_filters(app_name, True))
    not_installed_apps = sorted(
        app_name for app_name in apps.keys() if app_name not in installed_apps and matches_search_filters(app_name, False)
    )
    add_icons(installed_sorted, installed_icons_frame)
    add_icons(not_installed_apps, not_installed_icons_frame)
    empty_state = "Arama veya filtre ile eşleşen uygulama bulunamadı."
    if not installed_sorted:
        ctk.CTkLabel(installed_icons_frame, text=empty_state, text_color=THEME["muted"], font=(FONT, 11)).grid(row=0, column=0, padx=12, pady=12, sticky="w")
    if not not_installed_apps:
        ctk.CTkLabel(not_installed_icons_frame, text=empty_state, text_color=THEME["muted"], font=(FONT, 11)).grid(row=0, column=0, padx=12, pady=12, sticky="w")
    set_activate_idm_button_state(installed=IDM_APP_NAME in installed_apps)
    update_selected_app_highlight()


def matches_search_filters(app_name, is_installed):
    query = search_state["query"].strip().lower()
    if not query:
        return True
    app_id = apps[app_name]["id"].lower()
    alias_blob = " ".join(get_app_aliases(app_name, apps[app_name]["id"]))
    return query in app_name.lower() or query in app_id or query in alias_blob


def refresh_catalog_view():
    render_installed_apps(set(scan_cache["installed"]))


def sync_search_inputs(query):
    normalized_query = query or ""
    if selected_search_entry.get() != normalized_query:
        selected_search_entry.delete(0, "end")
        selected_search_entry.insert(0, normalized_query)


def set_search_query(value, source=None):
    normalized_value = value or ""
    search_state["query"] = normalized_value
    sync_search_inputs(normalized_value)
    refresh_catalog_view()


def add_history_item(action_name, target_name, result_status, detail_text):
    timestamp = time.strftime("%H:%M:%S")
    history_items.insert(0, {
        "time": timestamp,
        "action": action_name,
        "target": target_name,
        "status": result_status,
        "detail": detail_text,
    })
    del history_items[MAX_HISTORY_ITEMS:]
    save_history(history_items, MAX_HISTORY_ITEMS)
    app.after(0, render_history_view)


def clear_history_items():
    history_items.clear()
    save_history(history_items, MAX_HISTORY_ITEMS)
    render_history_view()


def get_history_status_style(status_name):
    mapping = {
        "success": (THEME["success_soft"], THEME["success"]),
        "warning": (THEME["accent_soft"], THEME["accent"]),
        "error": (THEME["danger_soft"], THEME["danger"]),
        "info": (THEME["surface_soft"], THEME["text"]),
    }
    return mapping.get(status_name, mapping["info"])


def set_history_filter(mode):
    history_filter_state["mode"] = mode
    update_history_filter_cards()
    render_history_view()


def update_history_filter_cards():
    card_map = {
        "all": globals().get("history_total_card"),
        "success": globals().get("history_success_card"),
        "issues": globals().get("history_issue_card"),
    }
    for key, card in card_map.items():
        if card is None:
            continue
        is_active = history_filter_state["mode"] == key
        card.configure(
            fg_color=THEME["accent_soft"] if is_active else THEME["surface_alt"],
            border_color=THEME["accent"] if is_active else THEME["border"],
        )


def render_history_view():
    container = globals().get("history_list_frame")
    total_value = globals().get("history_total_value")
    success_value = globals().get("history_success_value")
    issue_value = globals().get("history_issue_value")
    if container is None:
        return
    for widget in container.winfo_children():
        widget.destroy()
    total_count = len(history_items)
    success_count = sum(1 for item in history_items if item["status"] == "success")
    issue_count = sum(1 for item in history_items if item["status"] in {"warning", "error"})
    if total_value is not None:
        total_value.configure(text=str(total_count))
    if success_value is not None:
        success_value.configure(text=str(success_count))
    if issue_value is not None:
        issue_value.configure(text=str(issue_count))

    filter_mode = history_filter_state["mode"]
    if filter_mode == "success":
        filtered_items = [item for item in history_items if item["status"] == "success"]
        empty_state = "Başarılı işlem kaydı yok"
    elif filter_mode == "issues":
        filtered_items = [item for item in history_items if item["status"] in {"warning", "error"}]
        empty_state = "Uyarı veya hata kaydı yok"
    else:
        filtered_items = list(history_items)
        empty_state = "Henüz işlem kaydı yok"

    if not filtered_items:
        ctk.CTkLabel(container, text=empty_state, font=(FONT, 14, "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(6, 4))
        return

    for item in filtered_items:
        badge_bg, badge_text = get_history_status_style(item["status"])
        detail_text = item.get("detail") or "İşlem tamamlandı"
        
        row = ctk.CTkFrame(container, fg_color=THEME["surface"], corner_radius=10, border_width=1, border_color=THEME["border"])
        row.pack(fill="x", pady=(0, 2))

        accent = ctk.CTkFrame(row, fg_color=badge_bg, width=3, corner_radius=3)
        accent.pack(side="left", fill="y", padx=(0, 4), pady=2)

        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=1)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=item["action"], font=(FONT, 12, "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkLabel(top, text=item["time"], font=(FONT, 10), text_color=THEME["muted"]).pack(side="right")

        middle = ctk.CTkFrame(content, fg_color="transparent")
        middle.pack(fill="x", pady=(1, 0))
        badge = ctk.CTkLabel(middle, text=item["target"], fg_color=badge_bg, text_color=badge_text, corner_radius=6, height=18, font=(FONT, 10, "bold"))
        badge.pack(side="left")

        detail_label = ctk.CTkLabel(
            content,
            text=detail_text,
            font=(FONT, 11),
            text_color=THEME["muted"],
            justify="left",
            wraplength=520,
        )
        detail_label.pack(anchor="w", pady=(2, 0))
    
    # Scroll region'ı güncelle
    app.after(0, sync_history_scroll_region)


def switch_view(view_name):
    close_search_focus()
    current_view["name"] = view_name
    for key, frame in globals().get("content_views", {}).items():
        if key == view_name:
            frame.pack(fill="both", expand=True)
        else:
            frame.pack_forget()
    update_navigation_styles()


def update_navigation_styles():
    for key, parts in nav_items.items():
        is_active = current_view["name"] == key
        parts["button"].configure(
            fg_color=THEME["surface_soft"] if is_active else "transparent",
            text_color=THEME["text"] if is_active else THEME["muted"],
            hover_color=THEME["surface_hover"],
        )
        parts["underline"].configure(fg_color=THEME["accent"] if is_active else THEME["surface"])


def get_registry_display_names(use_cache=True):
    return service_get_registry_display_names(
        registry_cache,
        REGISTRY_CACHE_TTL_SEC,
        use_cache=use_cache,
        winreg_module=winreg,
        time_module=time,
    )


def get_registry_app_details(app_name, app_id):
    return service_get_registry_app_details(app_name, app_id, APP_ALIASES, winreg_module=winreg)


def get_winget_package_details(app_id):
    return service_get_winget_package_details(app_id, subprocess_module=subprocess, shutil_module=shutil)


def get_app_aliases(app_name, app_id):
    return service_get_app_aliases(app_name, app_id, APP_ALIASES)


def update_helper_button_visibility():
    if "helper_button" not in globals() or "app_list" not in globals():
        return
    should_show = helper_button_state["visible"]
    is_mapped = bool(helper_button.winfo_manager())
    if should_show and not is_mapped:
        helper_button.pack(anchor="w", padx=12, pady=(0, 6))
    elif not should_show and is_mapped:
        helper_button.pack_forget()


def update_activate_idm_button_visibility():
    if "activate_idm_button" not in globals():
        return
    should_show = activate_idm_button_state["visible"]
    is_mapped = bool(activate_idm_button.winfo_manager())
    if should_show and not is_mapped:
        activate_idm_button.pack(side="right")
    elif not should_show and is_mapped:
        activate_idm_button.pack_forget()


def set_interaction_enabled(enabled):
    state = "normal" if enabled else "disabled"
    for widget_name in ["scan_button", "update_all_button", "app_list", "selected_search_entry", "theme_menu", "language_menu"]:
        widget = globals().get(widget_name)
        if widget is None:
            continue
        try:
            widget.configure(state=state)
        except Exception as e:
            logger.warning(f"Widget state güncellenemedi: {e}")
            continue
    apply_action_button_states()
    for parts in nav_items.values():
        try:
            parts["button"].configure(state=state)
        except Exception as e:
            logger.warning(f"Nav button state güncellenemedi: {e}")
            continue


def apply_action_button_states():
    desired_states = {
        "install_button": selected_action_state["install"],
        "uninstall_button": selected_action_state["uninstall"],
        "update_button": selected_action_state["update"],
        "helper_button": "normal" if helper_button_state["enabled"] else "disabled",
        "activate_idm_button": "normal" if activate_idm_button_state["enabled"] else "disabled",
    }
    if operation_state["busy"]:
        desired_states = {name: "disabled" for name in desired_states}
    for widget_name, state in desired_states.items():
        widget = globals().get(widget_name)
        if widget is None:
            continue
        try:
            if widget_name == "install_button":
                enabled_style = {
                    "fg_color": THEME["success"],
                    "hover_color": THEME["success_hover"],
                    "text_color": THEME["button_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["success"],
                }
                disabled_style = {
                    "fg_color": THEME["button_disabled_bg"],
                    "hover_color": THEME["button_disabled_bg"],
                    "text_color": THEME["button_disabled_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["button_disabled_border"],
                }
            elif widget_name == "uninstall_button":
                enabled_style = {
                    "fg_color": THEME["danger"],
                    "hover_color": THEME["danger_hover"],
                    "text_color": THEME["button_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["danger"],
                }
                disabled_style = {
                    "fg_color": THEME["button_disabled_bg"],
                    "hover_color": THEME["button_disabled_bg"],
                    "text_color": THEME["button_disabled_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["button_disabled_border"],
                }
            elif widget_name == "update_button":
                enabled_style = {
                    "fg_color": THEME["accent"],
                    "hover_color": THEME["accent_hover"],
                    "text_color": THEME["button_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["accent"],
                }
                disabled_style = {
                    "fg_color": THEME["button_disabled_bg"],
                    "hover_color": THEME["button_disabled_bg"],
                    "text_color": THEME["button_disabled_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["button_disabled_border"],
                }
            elif widget_name == "activate_idm_button":
                enabled_style = {
                    "fg_color": THEME["accent"],
                    "hover_color": THEME["accent_hover"],
                    "text_color": THEME["button_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["accent"],
                }
                disabled_style = {
                    "fg_color": THEME["button_disabled_bg"],
                    "hover_color": THEME["button_disabled_bg"],
                    "text_color": THEME["button_disabled_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["button_disabled_border"],
                }
            else:
                enabled_style = {
                    "fg_color": THEME["surface_soft"],
                    "hover_color": THEME["surface_hover"],
                    "text_color": THEME["text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["border_strong"],
                }
                disabled_style = {
                    "fg_color": THEME["button_disabled_bg"],
                    "hover_color": THEME["button_disabled_bg"],
                    "text_color": THEME["button_disabled_text"],
                    "text_color_disabled": THEME["button_disabled_text"],
                    "border_color": THEME["button_disabled_border"],
                }
            widget.configure(**(enabled_style if state == "normal" else disabled_style))
            widget.configure(state=state)
        except Exception as e:
            logger.warning(f"Aksiyon butonu durumu güncellenemedi ({widget_name}): {e}")
    update_helper_button_visibility()
    update_activate_idm_button_visibility()


def set_action_button_states(installed=None, can_update=False, loading=False):
    if loading or installed is None:
        selected_action_state.update({"install": "disabled", "uninstall": "disabled", "update": "disabled"})
    elif installed:
        selected_action_state.update({
            "install": "disabled",
            "uninstall": "normal",
            "update": "normal" if can_update else "disabled",
        })
    else:
        selected_action_state.update({"install": "normal", "uninstall": "disabled", "update": "disabled"})
    apply_action_button_states()


def set_helper_button_state(selected_app, installed=False, loading=False):
    is_helper_app = selected_app == IDM_APP_NAME
    helper_button_state["visible"] = is_helper_app
    helper_button_state["enabled"] = is_helper_app and installed and not loading
    apply_action_button_states()


def set_activate_idm_button_state(installed=False):
    activate_idm_button_state["visible"] = installed
    activate_idm_button_state["enabled"] = installed
    apply_action_button_states()


def begin_operation(action_name):
    with operation_lock:
        if operation_state["busy"]:
            active_action = operation_state.get("action") or "Başka işlem"
            show_progress_modal("İşlem sürüyor", f"{active_action} tamamlanmadan yeni işlem başlatılamaz.", 0)
            progress_hint_label.configure(text="Lütfen mevcut işlemin bitmesini bekleyin.")
            app.after(1500, hide_progress_modal)
            return False
        operation_state["busy"] = True
        operation_state["action"] = action_name
    app.after(0, lambda: set_interaction_enabled(False))
    return True


def end_operation():
    with operation_lock:
        operation_state["busy"] = False
        operation_state["action"] = None
    app.after(0, lambda: set_interaction_enabled(True))


def get_installed_version(app_name, app_id):
    return service_get_installed_version(app_name, app_id, APP_ALIASES, winreg_module=winreg)


def has_available_upgrade(app_name, app_id):
    return service_has_available_upgrade(app_name, app_id, APP_ALIASES, subprocess_module=subprocess, shutil_module=shutil)


def get_bulk_update_candidates():
    return service_get_bulk_update_candidates(apps, APP_ALIASES, subprocess_module=subprocess, shutil_module=shutil)


def is_app_installed_via_winget(app_id):
    return service_is_app_installed_via_winget(app_id, subprocess_module=subprocess, shutil_module=shutil)


def run_helper_executable(exe_name):
    return service_run_helper_executable(
        exe_name,
        base_dir=resource_path(""),
        subprocess_module=subprocess,
        os_module=os,
    )


def get_installed_apps(force_refresh=False):
    if not scan_lock.acquire(blocking=False):
        return
    try:
        installed_apps, from_cache = get_installed_apps_snapshot(
            apps,
            APP_ALIASES,
            scan_cache,
            SCAN_CACHE_TTL_SEC,
            registry_cache,
            REGISTRY_CACHE_TTL_SEC,
            force_refresh=force_refresh,
            subprocess_module=subprocess,
            shutil_module=shutil,
            winreg_module=winreg,
            time_module=time,
        )
        if not installed_apps and shutil.which("winget") is None and winreg is None:
            return
        snapshot = set(installed_apps)
        app.after(0, lambda apps_snapshot=snapshot: render_installed_apps(apps_snapshot))
    except Exception as e:
        logger.error(f"Tarama sırasında hata: {e}")
    finally:
        scan_lock.release()


def threaded_get_installed_apps(force_refresh=False):
    threading.Thread(target=get_installed_apps, args=(force_refresh,), daemon=True).start()


def is_app_installed(app_name, app_id):
    return service_is_app_installed(
        app_name,
        app_id,
        APP_ALIASES,
        registry_cache,
        REGISTRY_CACHE_TTL_SEC,
        subprocess_module=subprocess,
        shutil_module=shutil,
        winreg_module=winreg,
        time_module=time,
    )


def run_winget_with_live_progress(cmd, selected_app, action_text):
    full_output = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding=None, errors="replace")
    ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    percent_re = re.compile(r"(\d{1,3})\s*%")
    size_re = re.compile(r"(\d+(?:[\.,]\d+)?)\s*(KB|MB|GB)\s*/\s*(\d+(?:[\.,]\d+)?)\s*(KB|MB|GB)", re.IGNORECASE)
    start_time = time.time()
    last_progress = 0.0
    saw_real_progress = False
    app.after(0, lambda: show_progress_modal(f"{selected_app} {action_text.title()}", f"{selected_app} için işlem hazırlanıyor...", 0))

    def normalize_console_line(line):
        line = ansi_re.sub("", line)
        return " ".join(line.strip().split())

    def update_live_status(line):
        nonlocal last_progress, saw_real_progress
        clean_line = normalize_console_line(line)
        if not clean_line:
            return
        full_output.append(clean_line)
        elapsed = int(time.time() - start_time)
        elapsed_text = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        percent_match = percent_re.search(clean_line)
        size_match = size_re.search(clean_line)
        detail_text = f"{selected_app} {action_text}..."
        if percent_match:
            percent_value = max(0, min(100, int(percent_match.group(1))))
            progress_value = percent_value / 100.0
            last_progress = progress_value
            saw_real_progress = True
            if size_match:
                downloaded = f"{size_match.group(1)} {size_match.group(2).upper()}"
                total = f"{size_match.group(3)} {size_match.group(4).upper()}"
                detail_text = f"{selected_app} {action_text}... %{percent_value} ({downloaded} / {total})"
            else:
                detail_text = f"{selected_app} {action_text}... %{percent_value}"
            app.after(0, lambda value=progress_value: update_progress_modal(progress=value))
        elif size_match:
            downloaded = f"{size_match.group(1)} {size_match.group(2).upper()}"
            total = f"{size_match.group(3)} {size_match.group(4).upper()}"
            detail_text = f"{selected_app} {action_text}... ({downloaded} / {total})"
            if last_progress < 0.95:
                last_progress = min(last_progress + 0.02, 0.95)
                app.after(0, lambda value=last_progress: update_progress_modal(progress=value))
        else:
            if last_progress < 0.9:
                last_progress = min(last_progress + 0.01, 0.9)
                app.after(0, lambda value=last_progress: update_progress_modal(progress=value))
        app.after(0, lambda text=detail_text: update_progress_modal(detail_text=text))
        app.after(0, lambda meta=f"Süre: {elapsed_text} | Son çıktı: {clean_line[:110]}": progress_hint_label.configure(text=meta))

    buffer = ""
    while True:
        chunk = process.stdout.read(1)
        if chunk == "":
            if process.poll() is not None:
                break
            continue
        if chunk in ("\r", "\n"):
            if buffer:
                update_live_status(buffer)
                buffer = ""
        else:
            buffer += chunk
    if buffer:
        update_live_status(buffer)
    if not saw_real_progress:
        app.after(0, lambda: progress_hint_label.configure(text="Canlı ilerleme verisi sınırlı geldi; kurucu pencere aşamasında olabilir."))
    return process.returncode, "\n".join(full_output)


def show_progress_modal(title_text, detail_text="", progress=0.0):
    presenter_show_progress_modal(
        progress_title_label,
        progress_detail_label,
        progress_modal_bar,
        progress_hint_label,
        progress_overlay,
        progress_card,
        title_text,
        detail_text,
        progress,
    )


def update_progress_modal(title_text=None, detail_text=None, progress=None):
    presenter_update_progress_modal(
        progress_title_label,
        progress_detail_label,
        progress_modal_bar,
        title_text=title_text,
        detail_text=detail_text,
        progress=progress,
    )


def hide_progress_modal():
    presenter_hide_progress_modal(progress_overlay)


def apply_operation_feedback(action_name, target_name, feedback, refresh_scan=False, refresh_details=False, hide_delay_ms=1800):
    presenter_apply_operation_feedback(
        app.after,
        lambda title, detail, progress: update_progress_modal(title, detail, progress),
        lambda hint: progress_hint_label.configure(text=hint),
        add_history_item,
        hide_progress_modal,
        action_name,
        target_name,
        feedback,
        refresh_scan_callback=threaded_get_installed_apps if refresh_scan else None,
        refresh_details_callback=refresh_selected_app_details if refresh_details else None,
        hide_delay_ms=hide_delay_ms,
    )


def manage_app(action):
    selected_app = app_list.get()
    if selected_app not in apps:
        return
    app_id = apps[selected_app]["id"]
    action_label, operation_name = get_manage_action_meta(action)
    if not begin_operation(operation_name):
        return
    show_progress_modal(f"{selected_app} {action_label.title()}", f"{selected_app} için işlem başlatıldı.", 0)

    def process():
        try:
            winget_path = shutil.which("winget")
            if winget_path is None:
                apply_operation_feedback(
                    operation_name,
                    selected_app,
                    {
                        "title": "İşlem başlatılamadı",
                        "detail": "winget komutu sistemde yok.",
                        "progress": 0,
                        "history_status": "error",
                        "history_detail": "winget komutu bulunamadığı için işlem başlatılamadı.",
                    },
                    hide_delay_ms=1500,
                )
                return
            currently_installed = is_app_installed(selected_app, app_id)
            currently_installed_via_winget = is_app_installed_via_winget(app_id)
            precheck_feedback = manage_precheck(action, currently_installed, currently_installed_via_winget, selected_app, operation_name)
            if precheck_feedback:
                precheck_feedback["progress"] = 0
                apply_operation_feedback(
                    operation_name,
                    selected_app,
                    precheck_feedback,
                    refresh_scan=precheck_feedback.get("refresh_scan", False),
                    hide_delay_ms=precheck_feedback["delay_ms"],
                )
                return
            cmd = build_manage_command(winget_path, action, app_id)
            return_code, full_output = run_winget_with_live_progress(cmd, selected_app, action_label)
            output_text = (full_output or "").lower()
            is_cancelled = output_contains_any(output_text, CANCEL_TOKENS)
            installed_now = is_app_installed(selected_app, app_id)
            result_feedback = manage_result(action, installed_now, is_cancelled, return_code, output_text, selected_app)
            result_feedback["progress"] = 1 if result_feedback["history_status"] == "success" else 0
            apply_operation_feedback(
                operation_name,
                selected_app,
                result_feedback,
                refresh_scan=True,
                refresh_details=True,
            )
        finally:
            end_operation()

    threading.Thread(target=process, daemon=True).start()

def update_app():
    selected_app = app_list.get()
    if selected_app not in apps:
        return
    app_id = apps[selected_app]["id"]
    if not begin_operation("Güncelleme"):
        return
    show_progress_modal(f"{selected_app} Güncelleniyor", f"{selected_app} için güncelleme başlatıldı.", 0)

    def process():
        try:
            winget_path = shutil.which("winget")
            if winget_path is None:
                apply_operation_feedback(
                    "Güncelleme",
                    selected_app,
                    {
                        "title": "Güncelleme başlatılamadı",
                        "detail": "winget komutu sistemde yok.",
                        "progress": 0,
                        "history_status": "error",
                        "history_detail": "winget komutu bulunamadığı için güncelleme başlatılamadı.",
                    },
                    hide_delay_ms=1500,
                )
                return

            currently_installed = is_app_installed(selected_app, app_id)
            currently_installed_via_winget = is_app_installed_via_winget(app_id)
            precheck_feedback = update_precheck(currently_installed, currently_installed_via_winget, selected_app)
            if precheck_feedback:
                precheck_feedback["progress"] = 0
                apply_operation_feedback(
                    "Güncelleme",
                    selected_app,
                    precheck_feedback,
                    refresh_scan=precheck_feedback.get("refresh_scan", False),
                    hide_delay_ms=precheck_feedback["delay_ms"],
                )
                return

            upgrade_available, upgrade_status = has_available_upgrade(selected_app, app_id)
            if not upgrade_available and upgrade_status == "up_to_date":
                apply_operation_feedback(
                    "Güncelleme",
                    selected_app,
                    {
                        "title": "Zaten güncel",
                        "detail": f"{selected_app} için yeni sürüm bulunmadı.",
                        "hint": "winget yeni sürüm tespit etmedi.",
                        "progress": 1,
                        "history_status": "info",
                        "history_detail": "Uygulama için yeni sürüm bulunmadı.",
                    },
                    refresh_details=True,
                    hide_delay_ms=1500,
                )
                return

            version_before = get_installed_version(selected_app, app_id)
            cmd = build_upgrade_command(winget_path, app_id)
            return_code, full_output = run_winget_with_live_progress(cmd, selected_app, "güncelleniyor")
            output_text = (full_output or "").lower()
            still_installed = is_app_installed(selected_app, app_id)
            version_after = get_installed_version(selected_app, app_id)

            result_feedback = update_result(return_code, still_installed, version_before, version_after, output_text, selected_app)
            result_feedback["progress"] = 1 if result_feedback["history_status"] in {"success", "info"} else 0
            apply_operation_feedback(
                "Güncelleme",
                selected_app,
                result_feedback,
                refresh_scan=True,
                refresh_details=True,
            )
        finally:
            end_operation()

    threading.Thread(target=process, daemon=True).start()


def run_idm_helper(show_progress=True, require_selected_idm=True):
    selected_app = app_list.get() if "app_list" in globals() else ""
    if require_selected_idm and selected_app != IDM_APP_NAME:
        return
    target_app = IDM_APP_NAME
    if not activate_idm_button_state["enabled"] and not helper_button_state["enabled"]:
        return
    if not begin_operation(IDM_HISTORY_ACTION_NAME):
        return
    if show_progress:
        show_progress_modal("Yardımcı araç çalıştırılıyor", "Internet Download Manager için yardımcı araç başlatıldı.", 0)

    def process():
        try:
            try:
                return_code, output_text = run_helper_executable("idm.exe")
            except FileNotFoundError:
                feedback = helper_missing_feedback("idm.exe")
                feedback["progress"] = 0
                feedback["history_detail"] = "IDM etkinleştirme başlatılamadı. idm.exe bulunamadı."
                apply_operation_feedback(
                    IDM_HISTORY_ACTION_NAME,
                    target_app,
                    feedback,
                    hide_delay_ms=1700,
                )
                return
            except Exception as e:
                feedback = helper_result(1, str(e))
                feedback["progress"] = 0
                feedback["history_detail"] = f"IDM etkinleştirme başarısız. Sebep: {str(e)}"
                apply_operation_feedback(
                    IDM_HISTORY_ACTION_NAME,
                    target_app,
                    feedback,
                    hide_delay_ms=1800,
                )
                return

            feedback = helper_result(return_code, output_text)
            feedback["progress"] = 1 if feedback["history_status"] == "success" else 0
            if feedback["history_status"] == "success":
                feedback["history_detail"] = "IDM etkinleştirme başarıyla tamamlandı."
            else:
                feedback["history_detail"] = feedback.get("history_detail", "IDM etkinleştirme başarısız.")
            apply_operation_feedback(
                IDM_HISTORY_ACTION_NAME,
                target_app,
                feedback,
                hide_delay_ms=1800,
            )
        finally:
            end_operation()

    threading.Thread(target=process, daemon=True).start()


def run_idm_helper_from_settings():
    run_idm_helper(show_progress=False, require_selected_idm=False)


def run_activation_helper_from_settings(target_name):
    if not begin_operation("Etkinleştirme"):
        return

    def process():
        try:
            try:
                return_code, output_text = run_helper_executable("active.cmd")
            except FileNotFoundError:
                feedback = helper_missing_feedback("active.cmd")
                feedback["progress"] = 0
                feedback["history_detail"] = f"{target_name} etkinleştirme başlatılamadı. active.cmd bulunamadı."
                apply_operation_feedback(
                    "Etkinleştirme",
                    target_name,
                    feedback,
                    hide_delay_ms=1700,
                )
                return
            except Exception as e:
                feedback = helper_result(1, str(e))
                feedback["progress"] = 0
                feedback["history_detail"] = f"{target_name} etkinleştirme başarısız. Sebep: {str(e)}"
                apply_operation_feedback(
                    "Etkinleştirme",
                    target_name,
                    feedback,
                    hide_delay_ms=1800,
                )
                return

            feedback = helper_result(return_code, output_text)
            feedback["progress"] = 1 if feedback["history_status"] == "success" else 0
            if feedback["history_status"] == "success":
                feedback["history_detail"] = f"{target_name} etkinleştirme başarıyla tamamlandı."
            else:
                feedback["history_detail"] = feedback.get("history_detail", f"{target_name} etkinleştirme başarısız.")
            apply_operation_feedback(
                "Etkinleştirme",
                target_name,
                feedback,
                hide_delay_ms=1800,
            )
        finally:
            end_operation()

    threading.Thread(target=process, daemon=True).start()


def run_windows_activation_helper():
    run_activation_helper_from_settings("Windows")


def run_office_activation_helper():
    run_activation_helper_from_settings("Office")


def update_all_apps():
    if not begin_operation("Toplu Güncelleme"):
        return
    show_progress_modal("Toplu güncelleme hazırlanıyor", "Katalogdaki uygulamalar için güncelleme adayları taranıyor.", 0)

    def process():
        try:
            winget_path = shutil.which("winget")
            if winget_path is None:
                apply_operation_feedback(
                    "Toplu Güncelleme",
                    "Katalog",
                    {
                        "title": "Toplu güncelleme başlatılamadı",
                        "detail": "winget komutu sistemde yok.",
                        "progress": 0,
                        "history_status": "error",
                        "history_detail": "winget komutu bulunamadığı için toplu güncelleme başlatılamadı.",
                    },
                    hide_delay_ms=1500,
                )
                return

            candidates, status = get_bulk_update_candidates()
            precheck_feedback = bulk_precheck(status if candidates else status)
            if not candidates:
                precheck_feedback["progress"] = 1 if precheck_feedback["history_status"] == "info" else 0
                apply_operation_feedback(
                    "Toplu Güncelleme",
                    "Katalog",
                    precheck_feedback,
                    hide_delay_ms=precheck_feedback["delay_ms"],
                )
                return

            success_count = 0
            skipped_count = 0
            failed_count = 0
            total = len(candidates)

            for index, app_name in enumerate(candidates, start=1):
                app_id = apps[app_name]["id"]
                if not is_app_installed_via_winget(app_id):
                    skipped_count += 1
                    add_history_item("Toplu Güncelleme", app_name, "warning", "winget paketi doğrulanamadığı için uygulama atlandı.")
                    continue

                version_before = get_installed_version(app_name, app_id)
                app.after(0, lambda current=index, total_count=total, label=app_name: update_progress_modal(
                    title_text=f"Toplu Güncelleme {current}/{total_count}",
                    detail_text=f"{label} için güncelleme başlatıldı.",
                    progress=(current - 1) / max(total_count, 1),
                ))
                cmd = build_upgrade_command(winget_path, app_id)
                return_code, output = run_winget_with_live_progress(cmd, app_name, f"güncelleniyor ({index}/{total})")
                output_text = (output or "").lower()
                version_after = get_installed_version(app_name, app_id)
                installed_now = is_app_installed(app_name, app_id)
                item_status, item_detail = bulk_item_result(return_code, version_before, version_after, installed_now, output_text)
                if item_status == "warning":
                    skipped_count += 1
                elif item_status == "success":
                    success_count += 1
                else:
                    failed_count += 1
                add_history_item("Toplu Güncelleme", app_name, item_status, item_detail)

            summary_text = summarize_bulk_update(success_count, skipped_count, failed_count)
            final_progress = 1 if failed_count == 0 else 0
            final_title = "Toplu güncelleme tamamlandı" if failed_count == 0 else "Toplu güncelleme tamamlandı"
            app.after(0, lambda text=summary_text, title=final_title, progress=final_progress: update_progress_modal(title, text, progress))
            app.after(0, lambda text=summary_text: progress_hint_label.configure(text=text))
            app.after(0, threaded_get_installed_apps)
            app.after(0, refresh_selected_app_details)
            app.after(2200, hide_progress_modal)
            add_history_item("Toplu Güncelleme", "Katalog", bulk_final_status(failed_count), summary_text)
        finally:
            end_operation()

    threading.Thread(target=process, daemon=True).start()


def set_info_value(widget, value):
    widget.configure(text=value if value else "Bilinmiyor")


def refresh_selected_app_details():
    selected_app = app_list.get()
    if selected_app not in apps:
        return

    set_action_button_states(loading=True)
    set_helper_button_state(selected_app, loading=True)
    update_helper_button_text()
    selected_app_title.configure(text=selected_app)
    app_id = apps[selected_app]["id"]
    selected_app_icon = build_icon(selected_app, 46)
    selected_logo_label.configure(image=selected_app_icon, text="")
    selected_logo_label.image = selected_app_icon
    app_id_value.configure(text=app_id)
    version_value.configure(text="Yükleniyor...")
    publisher_value.configure(text="Yükleniyor...")
    install_status_value.configure(text="Kontrol ediliyor...")

    def worker():
        installed = is_app_installed(selected_app, app_id)
        installed_via_winget = is_app_installed_via_winget(app_id) if installed else False
        can_update = False
        if installed and installed_via_winget:
            upgrade_available, _ = has_available_upgrade(selected_app, app_id)
            can_update = upgrade_available
        registry_details = get_registry_app_details(selected_app, app_id)
        winget_details = get_winget_package_details(app_id)

        version_text = registry_details.get("version") or winget_details.get("version") or "Bilinmiyor"
        publisher_text = registry_details.get("publisher") or winget_details.get("publisher") or "Bilinmiyor"
        status_text = get_install_status_text(installed)

        def apply_selected_app_state():
            if app_list.get() != selected_app:
                return
            set_info_value(version_value, version_text)
            set_info_value(publisher_value, publisher_text)
            set_info_value(install_status_value, status_text)
            set_action_button_states(installed=installed, can_update=can_update)
            set_helper_button_state(selected_app, installed=installed)
            update_helper_button_text()

        app.after(0, apply_selected_app_state)

    threading.Thread(target=worker, daemon=True).start()


progress_overlay = ctk.CTkFrame(shell_frame, fg_color=THEME["overlay"])

progress_card = ctk.CTkFrame(progress_overlay, fg_color=THEME["surface"], corner_radius=16, border_width=1, border_color=THEME["border"], width=360, height=196)
progress_card.place(relx=0.5, rely=0.5, anchor="center")
progress_card.pack_propagate(False)

progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
progress_inner.pack(fill="both", expand=True, padx=18, pady=18)

progress_badge = ctk.CTkLabel(progress_inner, text="İşlem Sürüyor", width=104, height=24, corner_radius=12, fg_color=THEME["progress_badge_bg"], text_color=THEME["progress_badge_text"], font=(FONT, 10, "bold"))
progress_badge.pack(anchor="w")

progress_title_label = ctk.CTkLabel(progress_inner, text="Hazırlanıyor...", font=(FONT, 16, "bold"), text_color=THEME["text"])
progress_title_label.pack(anchor="w", pady=(12, 4))

progress_detail_label = ctk.CTkLabel(progress_inner, text="İşlem başlatılıyor.", font=(FONT, 10), text_color=THEME["muted"], justify="left", wraplength=300)
progress_detail_label.pack(anchor="w")

progress_modal_bar = ctk.CTkProgressBar(progress_inner, height=12, progress_color=THEME["accent"], fg_color=THEME["border"])
progress_modal_bar.set(0)
progress_modal_bar.pack(fill="x", pady=(16, 8))

progress_hint_label = ctk.CTkLabel(progress_inner, text="Kurulum adımları canlı olarak burada gösterilir.", font=(FONT, 10), text_color=THEME["muted"])
progress_hint_label.pack(anchor="w")

signature_frame = ctk.CTkFrame(shell_frame, fg_color="transparent", height=52)
signature_frame.pack(fill="x", pady=(10, 0))
signature_frame.pack_propagate(False)
signature_canvas = tk.Canvas(signature_frame, width=360, height=28, bg=THEME["bg"], highlightthickness=0, bd=0, relief="flat")
signature_canvas.place(relx=0.5, rely=0.5, anchor="center")
signature_text_item = signature_canvas.create_text(
    0,
    14,
    text="Designed by Serhat Can   ",
    anchor="w",
    fill=THEME["signature_text"],
    font=("Bahnschrift SemiBold", 12, "bold"),
)
signature_animation = {"running": False, "x": 0}
github_button = ctk.CTkButton(signature_frame, text="", width=50, height=50, corner_radius=0, border_width=0, fg_color="transparent", hover_color=THEME["bg"], image=build_ui_icon("github.png", 30), command=lambda: open_external_link(GITHUB_URL))
github_button.place(relx=1.0, rely=0.5, x=-106, anchor="e")
linkedin_button = ctk.CTkButton(signature_frame, text="", width=50, height=50, corner_radius=0, border_width=0, fg_color="transparent", hover_color=THEME["bg"], image=build_ui_icon("linkedin.png", 30), command=lambda: open_external_link(LINKEDIN_URL))
linkedin_button.place(relx=1.0, rely=0.5, x=-58, anchor="e")
instagram_button = ctk.CTkButton(signature_frame, text="", width=50, height=50, corner_radius=0, border_width=0, fg_color="transparent", hover_color=THEME["bg"], image=build_ui_icon("instagram.png", 30), command=lambda: open_external_link(INSTAGRAM_URL))
instagram_button.place(relx=1.0, rely=0.5, x=-10, anchor="e")


def reset_signature_position(_event=None):
    canvas_width = signature_canvas.winfo_width()
    signature_animation["x"] = canvas_width - 8
    signature_canvas.coords(signature_text_item, signature_animation["x"], 14)


def animate_signature():
    if not signature_animation["running"]:
        return
    canvas_width = max(signature_canvas.winfo_width(), 1)
    text_bbox = signature_canvas.bbox(signature_text_item)
    text_width = (text_bbox[2] - text_bbox[0]) if text_bbox else 140
    next_x = signature_animation["x"] - 2
    if next_x < -text_width + 8:
        next_x = canvas_width - 8
    signature_animation["x"] = next_x
    signature_canvas.coords(signature_text_item, next_x, 14)
    app.after(28, animate_signature)


def start_signature_animation():
    if signature_animation["running"]:
        return
    signature_animation["running"] = True
    reset_signature_position()
    animate_signature()


signature_canvas.bind("<Configure>", reset_signature_position)


def update_language(language):
    global lang_texts
    lang_texts = load_language(language)
    ui_texts = get_ui_texts(lang_texts)
    install_button.configure(text=ui_texts["install_button"])
    uninstall_button.configure(text=ui_texts["uninstall_button"])
    update_button.configure(text=ui_texts["update_button"])
    scan_button.configure(text=ui_texts["scan_button"])
    installed_label.configure(text=ui_texts["installed_label"])
    not_installed_label.configure(text=ui_texts["not_installed_label"])
    nav_items["operations"]["button"].configure(text=ui_texts["nav_operations"])
    nav_items["history"]["button"].configure(text=ui_texts["nav_history"])
    nav_items["settings"]["button"].configure(text=ui_texts["nav_settings"])
    control_title.configure(text=ui_texts["nav_operations"])
    history_title.configure(text=ui_texts["nav_history"])
    history_clear_button.configure(text="Temizle")
    history_refresh_button.configure(text=ui_texts["history_refresh"])
    info_title.configure(text=ui_texts["info_title"])
    actions_title.configure(text=ui_texts["actions_title"])
    selected_search_entry.configure(placeholder_text=ui_texts["selected_search_placeholder"])
    update_all_button.configure(text=ui_texts["update_all_button"])
    update_helper_button_text()


def change_language(language):
    settings["language"] = language
    save_settings(settings)
    update_language(language)
    apply_language_theme_choices(language)


language_menu.set(settings.get("language", "Türkçe"))
update_language(settings["language"])
apply_language_theme_choices(settings["language"])
apply_theme_colors()
update_settings_content()
set_activate_idm_button_state(installed=False)
app_list.configure(command=select_app)
scan_button.configure(command=threaded_get_installed_apps)
update_button.configure(command=update_app)
helper_button.configure(command=run_idm_helper)
activate_idm_button.configure(command=run_idm_helper_from_settings)
update_all_button.configure(command=update_all_apps)
activate_windows_button.configure(command=run_windows_activation_helper)
activate_office_button.configure(command=run_office_activation_helper)
history_clear_button.configure(command=clear_history_items)
history_refresh_button.configure(command=render_history_view)
render_history_view()
switch_view("operations")
app.bind("<Configure>", handle_window_resize)
app.after(0, apply_responsive_layout)
refresh_selected_app_details()
threaded_get_installed_apps()
start_signature_animation()
app.mainloop()
