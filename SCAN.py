
import os
import re
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
)
from scan_ui_presenter import (
    apply_operation_feedback as presenter_apply_operation_feedback,
    hide_progress_modal as presenter_hide_progress_modal,
    show_progress_modal as presenter_show_progress_modal,
    update_progress_modal as presenter_update_progress_modal,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'scan.log')),
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
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "accent_soft": "#dbeafe",
            "accent_text": "#f8fbff",
            "success": "#1f8a4c",
            "success_hover": "#18733f",
            "success_soft": "#dcfce7",
            "danger": "#d14343",
            "danger_hover": "#b93535",
            "danger_soft": "#fee2e2",
            "button_text": "#ffffff",
            "input_button": "#d9e4f2",
            "input_button_hover": "#cad8ea",
            "overlay": "#d8e2f0",
            "selected_tile": "#dbeafe",
            "selected_tile_text": "#133772",
            "badge_installed_bg": "#dbeafe",
            "badge_installed_text": "#1d4ed8",
            "badge_ready_bg": "#dcfce7",
            "badge_ready_text": "#1f8a4c",
            "progress_badge_bg": "#dbeafe",
            "progress_badge_text": "#1d4ed8",
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
        "accent": "#4f8cff",
        "accent_hover": "#3b78ec",
        "accent_soft": "#1f3c68",
        "accent_text": "#f4f8ff",
        "success": "#2ba36a",
        "success_hover": "#23905d",
        "success_soft": "#173a2b",
        "danger": "#e05d5d",
        "danger_hover": "#c94c4c",
        "danger_soft": "#482127",
        "button_text": "#f4f8ff",
        "input_button": "#24344f",
        "input_button_hover": "#2b3f61",
        "overlay": "#0b1220",
        "selected_tile": "#203252",
        "selected_tile_text": "#f3f8ff",
        "badge_installed_bg": "#19345c",
        "badge_installed_text": "#7cb0ff",
        "badge_ready_bg": "#173a2b",
        "badge_ready_text": "#57d39a",
        "progress_badge_bg": "#19345c",
        "progress_badge_text": "#7cb0ff",
    }


THEME = get_theme_colors()
panel_canvases = []
panel_sections = []

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 760

app = ctk.CTk(fg_color=THEME["bg"])
app.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
app.title("SCAN")
app.resizable(False, False)
app.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
app.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)

icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
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
search_state = {"query": "", "status": "all"}
history_items = []
current_view = {"name": "operations"}
SCAN_CACHE_TTL_SEC = 12
REGISTRY_CACHE_TTL_SEC = 180
MAX_HISTORY_ITEMS = 12
lang_texts = {}
active_scroll_canvas = None
app_tile_widgets = {}
nav_items = {}
history_items = load_history(MAX_HISTORY_ITEMS)


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
        ("github_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("installed_frame", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("not_installed_frame", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("installed_label", {"text_color": THEME["text"]}),
        ("not_installed_label", {"text_color": THEME["text"]}),
        ("navigation_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("control_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("control_title", {"text_color": THEME["text"]}),
        ("scan_button", {"fg_color": THEME["surface_soft"], "hover_color": THEME["surface_hover"], "text_color": THEME["text"]}),
        ("update_all_button", {"fg_color": THEME["accent"], "hover_color": THEME["accent_hover"], "text_color": THEME["button_text"]}),
        ("search_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("search_label", {"text_color": THEME["muted"]}),
        ("search_entry", {"fg_color": THEME["surface"], "border_color": THEME["border"], "text_color": THEME["text"]}),
        ("filter_panel", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("filter_title", {"text_color": THEME["muted"]}),
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
        ("update_button", {"fg_color": THEME["surface_soft"], "hover_color": THEME["surface_hover"], "border_color": THEME["border_strong"], "text_color": THEME["text"]}),
        ("history_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("history_title", {"text_color": THEME["text"]}),
        ("history_subtitle", {"text_color": THEME["muted"]}),
        ("history_refresh_button", {"fg_color": THEME["surface_soft"], "hover_color": THEME["surface_hover"], "text_color": THEME["text"], "border_color": THEME["border"]}),
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
        ("settings_title", {"text_color": THEME["text"]}),
        ("settings_subtitle", {"text_color": THEME["muted"]}),
        ("appearance_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
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
        ("language_card", {"fg_color": THEME["surface_alt"], "border_color": THEME["border"]}),
        ("language_title", {"text_color": THEME["text"]}),
        ("language_desc", {"text_color": THEME["muted"]}),
        ("settings_note", {"text_color": THEME["muted"]}),
        ("progress_overlay", {"fg_color": THEME["overlay"]}),
        ("progress_card", {"fg_color": THEME["surface"], "border_color": THEME["border"]}),
        ("progress_badge", {"fg_color": THEME["progress_badge_bg"], "text_color": THEME["progress_badge_text"]}),
        ("progress_title_label", {"text_color": THEME["text"]}),
        ("progress_detail_label", {"text_color": THEME["muted"]}),
        ("progress_modal_bar", {"progress_color": THEME["accent"], "fg_color": THEME["border"]}),
        ("progress_hint_label", {"text_color": THEME["muted"]}),
        ("signature_label", {"text_color": THEME["muted"]}),
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

    if "selected_search_icon" in globals():
        draw_search_icon(selected_search_icon)

    for section in panel_sections:
        section["panel"].configure(fg_color=THEME["surface"], border_color=THEME["border"])
        section["badge"].configure(
            fg_color=THEME.get(section["badge_fg"], section["badge_fg"]),
            text_color=THEME.get(section["badge_text_color"], section["badge_text_color"]),
        )
        section["title"].configure(text_color=THEME["text"])
        section["desc"].configure(text_color=THEME["muted"])
        section["body"].configure(fg_color=THEME["surface"])
        section["content"].configure(fg_color=THEME["surface"])

    update_selected_app_highlight()
    update_navigation_styles()
    update_filter_buttons()
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
        logo_path = os.path.join(os.path.dirname(__file__), "icons", apps[app_name]["logo"])
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((size, size), Image.LANCZOS)
            icon_cache[cache_key] = CTkImage(light_image=img, dark_image=img, size=(size, size))
    return icon_cache.get(cache_key)


def create_panel(parent, badge_text, badge_fg, badge_text_color, title_text, description_text):
    global active_scroll_canvas
    resolved_badge_fg = THEME.get(badge_fg, badge_fg)
    resolved_badge_text_color = THEME.get(badge_text_color, badge_text_color)

    panel = ctk.CTkFrame(parent, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
    header = ctk.CTkFrame(panel, fg_color="transparent")
    header.pack(fill="x", padx=14, pady=(14, 8))
    badge = ctk.CTkLabel(header, text=badge_text, width=78, height=24, corner_radius=12, fg_color=resolved_badge_fg, text_color=resolved_badge_text_color, font=(FONT, 10, "bold"))
    badge.pack(anchor="w")
    title = ctk.CTkLabel(header, text=title_text, font=(FONT, 15, "bold"), text_color=THEME["text"])
    title.pack(anchor="w", pady=(8, 2))
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
        "badge": badge,
        "badge_fg": badge_fg,
        "badge_text_color": badge_text_color,
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

toolbar_row = ctk.CTkFrame(control_inner, fg_color="transparent")
search_card = ctk.CTkFrame(toolbar_row, fg_color=THEME["surface_alt"], corner_radius=12, border_width=1, border_color=THEME["border"])
search_card.pack(side="left", fill="x", expand=True, padx=(0, 8))
search_inner = ctk.CTkFrame(search_card, fg_color="transparent")
search_inner.pack(fill="x", padx=12, pady=10)
search_label = ctk.CTkLabel(search_inner, text="Ara", font=(FONT, 10, "bold"), text_color=THEME["muted"])
search_label.pack(anchor="w")
search_var = tk.StringVar()
search_var.trace_add("write", lambda *_args: set_search_query(search_var.get()))
search_entry = ctk.CTkEntry(search_inner, textvariable=search_var, placeholder_text="Uygulama adı veya paket kimliği ile ara", height=36, corner_radius=10, fg_color=THEME["surface"], border_color=THEME["border"], text_color=THEME["text"])
search_entry.pack(fill="x", pady=(8, 0))

filter_panel = ctk.CTkFrame(toolbar_row, fg_color=THEME["surface_alt"], corner_radius=12, border_width=1, border_color=THEME["border"], width=320)
filter_panel.pack(side="left", fill="y", padx=(8, 0))
filter_panel.pack_propagate(False)
filter_inner = ctk.CTkFrame(filter_panel, fg_color="transparent")
filter_inner.pack(fill="both", expand=True, padx=12, pady=10)
filter_title = ctk.CTkLabel(filter_inner, text="Filtre", font=(FONT, 10, "bold"), text_color=THEME["muted"])
filter_title.pack(anchor="w")
filter_row = ctk.CTkFrame(filter_inner, fg_color="transparent")
filter_row.pack(fill="x", pady=(8, 0))
filter_buttons = {}
for key, label in [("all", "Tümü"), ("installed", "Kurulu"), ("ready", "Hazır")]:
    button = ctk.CTkButton(filter_row, text=label, command=lambda selected=key: set_status_filter(selected), width=90, height=34, corner_radius=10, border_width=1, fg_color=THEME["surface_soft"], hover_color=THEME["surface_hover"], border_color=THEME["border"], text_color=THEME["text"], font=(FONT, 10, "bold"))
    button.pack(side="left", padx=(0, 8))
    filter_buttons[key] = button

action_row = ctk.CTkFrame(control_inner, fg_color="transparent")
action_row.pack(fill="x", pady=(12, 0))

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
selected_search_entry.bind("<KeyRelease>", lambda _event: set_search_query(selected_search_entry.get()))
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

actions_panel = ctk.CTkFrame(action_row, fg_color=THEME["surface_alt"], corner_radius=12, border_width=1, border_color=THEME["border"])
actions_panel.pack(side="left", fill="y", padx=(8, 0))
actions_title = ctk.CTkLabel(actions_panel, text="İşlemler", font=(FONT, 11, "bold"), text_color=THEME["muted"])
actions_title.pack(anchor="w", padx=12, pady=(10, 8))
install_button = ctk.CTkButton(actions_panel, text="Yükle", width=130, height=34, corner_radius=10, fg_color=THEME["success"], hover_color=THEME["success_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: manage_app("install"))
install_button.pack(anchor="w", padx=12, pady=(0, 8))
uninstall_button = ctk.CTkButton(actions_panel, text="Kaldır", width=130, height=34, corner_radius=10, fg_color=THEME["danger"], hover_color=THEME["danger_hover"], text_color=THEME["button_text"], font=(FONT, 11, "bold"), command=lambda: manage_app("uninstall"))
uninstall_button.pack(anchor="w", padx=12, pady=(0, 8))
update_button = ctk.CTkButton(actions_panel, text="Güncelle", width=130, height=34, corner_radius=10, fg_color=THEME["surface_soft"], hover_color=THEME["surface_hover"], border_width=1, border_color=THEME["border_strong"], text_color=THEME["text"], font=(FONT, 11, "bold"))
update_button.pack(anchor="w", padx=12, pady=(0, 12))

main_frame = ctk.CTkFrame(operations_view, fg_color="transparent")
main_frame.pack(fill="both", expand=True)
panel_row = ctk.CTkFrame(main_frame, fg_color="transparent")
panel_row.pack(fill="both", expand=True)
installed_frame, installed_label, installed_icons_frame = create_panel(panel_row, "Kurulu", "badge_installed_bg", "badge_installed_text", "Yüklü Uygulamalar", "Sisteminizde bulunan uygulamalar burada görünür.")
installed_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
not_installed_frame, not_installed_label, not_installed_icons_frame = create_panel(panel_row, "Hazır", "badge_ready_bg", "badge_ready_text", "Yüklü Olmayan Uygulamalar", "Kurulabilir uygulamaları bu panelden takip edebilirsiniz.")
not_installed_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

history_card = ctk.CTkFrame(history_view, fg_color=THEME["surface"], corner_radius=14, border_width=1, border_color=THEME["border"])
history_card.pack(fill="both", expand=True)
history_inner = ctk.CTkFrame(history_card, fg_color="transparent")
history_inner.pack(fill="both", expand=True, padx=14, pady=14)
history_header = ctk.CTkFrame(history_inner, fg_color="transparent")
history_header.pack(fill="x")
history_title = ctk.CTkLabel(history_header, text="Son İşlemler", font=(FONT, 16, "bold"), text_color=THEME["text"])
history_title.pack(side="left")
history_refresh_button = ctk.CTkButton(history_header, text="Yenile", width=96, height=32, corner_radius=10, border_width=1, fg_color=THEME["surface_soft"], hover_color=THEME["surface_hover"], border_color=THEME["border"], text_color=THEME["text"], font=(FONT, 10, "bold"))
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
settings_title = ctk.CTkLabel(settings_inner, text="Ayarlar", font=(FONT, 16, "bold"), text_color=THEME["text"])
settings_title.pack(anchor="w")
settings_subtitle = ctk.CTkLabel(settings_inner, text="Görünümü ve dil tercihlerini mevcut pencere içinde yönetin.", font=(FONT, 10), text_color=THEME["muted"])
settings_subtitle.pack(anchor="w", pady=(6, 12))
settings_grid = ctk.CTkFrame(settings_inner, fg_color="transparent")
settings_grid.pack(fill="x")
appearance_card = ctk.CTkFrame(settings_grid, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
appearance_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
appearance_inner = ctk.CTkFrame(appearance_card, fg_color="transparent")
appearance_inner.pack(fill="both", expand=True, padx=14, pady=14)
appearance_title = ctk.CTkLabel(appearance_inner, text="Görünüm", font=(FONT, 12, "bold"), text_color=THEME["text"])
appearance_title.pack(anchor="w")
appearance_desc = ctk.CTkLabel(appearance_inner, text="Açık veya koyu modu seçin.", font=(FONT, 10), text_color=THEME["muted"])
appearance_desc.pack(anchor="w", pady=(4, 10))
theme_menu = ctk.CTkOptionMenu(appearance_inner, values=["Dark", "Light"], command=change_theme, width=180, height=36, fg_color=THEME["surface"], button_color=THEME["input_button"], button_hover_color=THEME["input_button_hover"], dropdown_fg_color=THEME["surface"], dropdown_hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
theme_menu.pack(anchor="w")

language_card = ctk.CTkFrame(settings_grid, fg_color=THEME["surface_alt"], corner_radius=14, border_width=1, border_color=THEME["border"])
language_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
language_inner = ctk.CTkFrame(language_card, fg_color="transparent")
language_inner.pack(fill="both", expand=True, padx=14, pady=14)
language_title = ctk.CTkLabel(language_inner, text="Dil", font=(FONT, 12, "bold"), text_color=THEME["text"])
language_title.pack(anchor="w")
language_desc = ctk.CTkLabel(language_inner, text="Arayüz dilini buradan değiştirin.", font=(FONT, 10), text_color=THEME["muted"])
language_desc.pack(anchor="w", pady=(4, 10))
language_menu = ctk.CTkOptionMenu(language_inner, values=["Türkçe", "English", "Русский", "Deutsch", "中文", "Español", "العربية"], command=lambda language: change_language(language), width=180, height=36, fg_color=THEME["surface"], button_color=THEME["input_button"], button_hover_color=THEME["input_button_hover"], dropdown_fg_color=THEME["surface"], dropdown_hover_color=THEME["surface_hover"], text_color=THEME["text"], font=(FONT, 11, "bold"))
language_menu.pack(anchor="w")
settings_note = ctk.CTkLabel(settings_inner, text="Yeni pencere açılmaz; görünüm değişiklikleri doğrudan mevcut ekranda uygulanır.", font=(FONT, 10), text_color=THEME["muted"])
settings_note.pack(anchor="w", pady=(12, 0))


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

        # Sadece yüklü uygulamalarda güncelleme kontrolü yap
        if app_name in scan_cache.get("installed", []):
            def check_update(app_n=app_name, app_i=apps[app_name]["id"], tile_widget=tile):
                try:
                    upgrade_available, _ = has_available_upgrade(app_n, app_i)
                    if upgrade_available:
                        def create_badge():
                            badge_label = ctk.CTkLabel(tile_widget, text="●", text_color=THEME["surface_soft"], font=(FONT, 10, "bold"), width=16, height=16, fg_color=THEME["danger"], corner_radius=8)
                            badge_label.place(relx=0.9, rely=0.05, anchor="ne")
                        app.after(0, create_badge)
                except Exception as e:
                    logger.debug(f"Güncelleme rozeti kontrolü başarısız ({app_n}): {e}")

            threading.Thread(target=check_update, daemon=True).start()

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
    update_selected_app_highlight()


def matches_search_filters(app_name, is_installed):
    query = search_state["query"].strip().lower()
    status = search_state["status"]
    if status == "installed" and not is_installed:
        return False
    if status == "ready" and is_installed:
        return False
    if not query:
        return True
    app_id = apps[app_name]["id"].lower()
    alias_blob = " ".join(get_app_aliases(app_name, apps[app_name]["id"]))
    return query in app_name.lower() or query in app_id or query in alias_blob


def refresh_catalog_view():
    render_installed_apps(set(scan_cache["installed"]))


def set_search_query(value):
    search_state["query"] = value or ""
    refresh_catalog_view()


def set_status_filter(status_key):
    search_state["status"] = status_key
    update_filter_buttons()
    refresh_catalog_view()


def update_filter_buttons():
    filter_meta = {
        "all": ("Tümü", THEME["accent"], THEME["button_text"], THEME["accent"]),
        "installed": ("Kurulu", THEME["accent"], THEME["button_text"], THEME["accent"]),
        "ready": ("Hazır", THEME["accent"], THEME["button_text"], THEME["accent"]),
    }
    for key, button in globals().get("filter_buttons", {}).items():
        is_active = search_state["status"] == key
        button.configure(
            fg_color=filter_meta[key][1] if is_active else THEME["surface_soft"],
            text_color=filter_meta[key][2] if is_active else THEME["text"],
            border_color=filter_meta[key][3] if is_active else THEME["border"],
        )


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


def get_history_status_style(status_name):
    mapping = {
        "success": (THEME["success_soft"], THEME["success"]),
        "warning": (THEME["accent_soft"], THEME["accent"]),
        "error": (THEME["danger_soft"], THEME["danger"]),
        "info": (THEME["surface_soft"], THEME["text"]),
    }
    return mapping.get(status_name, mapping["info"])


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

    if not history_items:
        ctk.CTkLabel(container, text="Henüz işlem kaydı yok", font=(FONT, 14, "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(6, 4))
        return

    for item in history_items:
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

def scan_registry_uninstall(root, subkey):
    names = []
    if winreg is None:
        return names
    try:
        with winreg.OpenKey(root, subkey) as key:
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                try:
                    skey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, skey_name) as sk:
                        try:
                            display_name = winreg.QueryValueEx(sk, "DisplayName")[0]
                            names.append(display_name)
                        except Exception:
                            pass
                except Exception:
                    continue
    except Exception:
        pass
    return names


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


def set_interaction_enabled(enabled):
    state = "normal" if enabled else "disabled"
    for widget_name in ["install_button", "uninstall_button", "update_button", "scan_button", "update_all_button", "app_list", "search_entry", "selected_search_entry", "theme_menu", "language_menu"]:
        widget = globals().get(widget_name)
        if widget is None:
            continue
        try:
            widget.configure(state=state)
        except Exception as e:
            logger.warning(f"Widget state güncellenemedi: {e}")
            continue
    for button in globals().get("filter_buttons", {}).values():
        try:
            button.configure(state=state)
        except Exception as e:
            logger.warning(f"Filter button state güncellenemedi: {e}")
            continue
    for parts in nav_items.values():
        try:
            parts["button"].configure(state=state)
        except Exception as e:
            logger.warning(f"Nav button state güncellenemedi: {e}")
            continue


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
        refresh_scan_callback=(lambda: threaded_get_installed_apps(force_refresh=True)) if refresh_scan else None,
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
            app.after(0, lambda: threaded_get_installed_apps(force_refresh=True))
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
        registry_details = get_registry_app_details(selected_app, app_id)
        winget_details = get_winget_package_details(app_id)

        version_text = registry_details.get("version") or winget_details.get("version") or "Bilinmiyor"
        publisher_text = registry_details.get("publisher") or winget_details.get("publisher") or "Bilinmiyor"
        status_text = get_install_status_text(installed)

        app.after(0, lambda: set_info_value(version_value, version_text))
        app.after(0, lambda: set_info_value(publisher_value, publisher_text))
        app.after(0, lambda: set_info_value(install_status_value, status_text))

    threading.Thread(target=worker, daemon=True).start()


progress_overlay = ctk.CTkFrame(shell_frame, fg_color=THEME["overlay"])

progress_card = ctk.CTkFrame(progress_overlay, fg_color=THEME["surface"], corner_radius=16, border_width=1, border_color=THEME["border"], width=360, height=170)
progress_card.place(relx=0.5, rely=0.5, anchor="center")
progress_card.pack_propagate(False)

progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
progress_inner.pack(fill="both", expand=True, padx=18, pady=16)

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

signature_frame = ctk.CTkFrame(shell_frame, fg_color="transparent")
signature_frame.pack(fill="x", pady=(10, 0))
signature_label = ctk.CTkLabel(signature_frame, text="Designed by Serhat-Can", font=(FONT, 11), text_color=THEME["muted"])
signature_label.pack(anchor="e")


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
    history_refresh_button.configure(text=ui_texts["history_refresh"])
    settings_title.configure(text=ui_texts["nav_settings"])
    info_title.configure(text=ui_texts["info_title"])
    actions_title.configure(text=ui_texts["actions_title"])
    filter_title.configure(text=ui_texts["filter_title"])
    search_label.configure(text=ui_texts["search_label"])
    search_entry.configure(placeholder_text=ui_texts["search_placeholder"])
    selected_search_entry.configure(placeholder_text=ui_texts["selected_search_placeholder"])
    update_all_button.configure(text=ui_texts["update_all_button"])
    filter_buttons["all"].configure(text=ui_texts["filter_all"])
    filter_buttons["installed"].configure(text=ui_texts["filter_installed"])
    filter_buttons["ready"].configure(text=ui_texts["filter_ready"])


def change_language(language):
    settings["language"] = language
    save_settings(settings)
    update_language(language)
    apply_language_theme_choices(language)


language_menu.set(settings.get("language", "Türkçe"))
update_language(settings["language"])
apply_language_theme_choices(settings["language"])
apply_theme_colors()
app_list.configure(command=select_app)
scan_button.configure(command=threaded_get_installed_apps)
update_button.configure(command=update_app)
update_all_button.configure(command=update_all_apps)
history_refresh_button.configure(command=render_history_view)
update_all_button.pack_forget()
toolbar_row.pack_forget()
update_filter_buttons()
render_history_view()
switch_view("operations")
refresh_selected_app_details()
threaded_get_installed_apps()
app.mainloop()
