import subprocess
import customtkinter as ctk
import os
from PIL import Image, ImageTk
import threading
import webbrowser  # GitHub linki için
import json
from customtkinter import CTkImage  # CTkImage'i import edin
import random
from concurrent.futures import ThreadPoolExecutor
import shutil
import re
import time
try:
    import winreg
except Exception:
    winreg = None


# Tkinter ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Ana pencere oluştur
app = ctk.CTk()
app.geometry("800x700+{}+{}".format(int(app.winfo_screenwidth() / 2 - 350), int(app.winfo_screenheight() / 2 - 380)))
app.title("SCAN")
app.resizable(False, False)

# Programın logosunu ayarla (ikon yoksa hatayı yakalayacak)
icon_path = r"c:\Users\canse\OneDrive\Desktop\UygulamaYükleme\app_icon.ico"
try:
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)  # Tam yol
except Exception:
    # İkon yüklenemezse uygulamanın çökmesini engelle
    pass

# Ayar dosyasının yolu
SETTINGS_DIR = r"C:\scanapp"
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")

# Kullanıcı ayarlarını yükle
def load_settings():
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            settings = json.load(f)
            # Varsayılan olarak Türkçe dilini ayarla
            settings["language"] = "Türkçe"
            return settings
    # Eğer settings.json yoksa varsayılan ayarları döndür
    return {"language": "Türkçe", "Theme": "Dark"}

# Kullanıcı ayarlarını kaydet
def save_settings(settings):
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f)

# Ayarları yükle
settings = load_settings()
save_settings(settings)  # Varsayılan ayarları kaydet

# Dil dosyasını yükleme fonksiyonu
def load_language(language):
    lang_file_path = os.path.join(os.path.dirname(__file__), "languages.json")
    if not os.path.exists(lang_file_path):
        raise FileNotFoundError(f"languages.json dosyası bulunamadı: {lang_file_path}")
    with open(lang_file_path, "r", encoding="utf-8") as f:
        return json.load(f).get(language, {})

# Dil güncelleme fonksiyonu
def update_language(language):
    global lang_texts
    lang_texts = load_language(language)

    # Buton ve etiket metinlerini güncelle
    install_button.configure(text=lang_texts["install"])
    uninstall_button.configure(text=lang_texts["uninstall"])
    update_button.configure(text=lang_texts["update"])
    scan_button.configure(text=lang_texts["scan"])
    status_label.configure(text=lang_texts["status"])
    installed_label.configure(text=lang_texts["installed_apps"])
    not_installed_label.configure(text=lang_texts["not_installed_apps"])

# Tema, dil ve GitHub butonlarını içeren çerçeve
top_frame = ctk.CTkFrame(app)
top_frame.pack(pady=10)

# Tema seçimi
def change_theme(theme):
    if theme == "Koyu" or theme == "Dark" or theme == "Тёмная" or theme == "Dunkel" or theme == "深色" or theme == "Oscuro" or theme == "داكن":
        ctk.set_appearance_mode("dark")
        settings["Theme"] = "Dark"
    elif theme == "Açık" or theme == "Light" or theme == "Светлая" or theme == "Hell" or theme == "浅色" or theme == "Claro" or theme == "فاتح":
        ctk.set_appearance_mode("light")
        settings["Theme"] = "Light"
    save_settings(settings)

# Dil seçimi
def change_language(language):
    settings["language"] = language
    save_settings(settings)
    update_language(language)

    # Tema adlarını dil seçimine göre güncelle
    if language == "Türkçe":
        theme_menu.configure(values=["Koyu", "Açık"])
        theme_menu.set("Koyu" if settings["Theme"] == "Dark" else "Açık")
    elif language == "English":
        theme_menu.configure(values=["Dark", "Light"])
        theme_menu.set("Dark" if settings["Theme"] == "Dark" else "Light")
    elif language == "Русский":
        theme_menu.configure(values=["Тёмная", "Светлая"])
        theme_menu.set("Тёмная" if settings["Theme"] == "Dark" else "Светлая")
    elif language == "Deutsch":
        theme_menu.configure(values=["Dunkel", "Hell"])
        theme_menu.set("Dunkel" if settings["Theme"] == "Dark" else "Hell")
    elif language == "中文":
        theme_menu.configure(values=["深色", "浅色"])
        theme_menu.set("深色" if settings["Theme"] == "Dark" else "浅色")
    elif language == "Español":
        theme_menu.configure(values=["Oscuro", "Claro"])
        theme_menu.set("Oscuro" if settings["Theme"] == "Dark" else "Claro")
    elif language == "العربية":
        theme_menu.configure(values=["داكن", "فاتح"])
        theme_menu.set("داكن" if settings["Theme"] == "Dark" else "فاتح")

# Tema menüsü
theme_menu = ctk.CTkOptionMenu(
    top_frame,
    values=["Dark", "Light"],  # Varsayılan değerler
    command=change_theme
)
theme_menu.grid(row=0, column=0, padx=5)

# Dil menüsü
language_menu = ctk.CTkOptionMenu(
    top_frame,
    values=["Türkçe", "English", "Русский", "Deutsch", "中文", "Español", "العربية"],
    command=change_language
)
language_menu.set(settings.get("language", "Türkçe"))
language_menu.grid(row=0, column=1, padx=5)

# GitHub'a yönlendiren buton
def open_github():
    webbrowser.open("https://github.com/serhatcan44")

github_button = ctk.CTkButton(top_frame, text="GitHub", command=open_github)
github_button.grid(row=0, column=2, padx=5)

# Uygulama listesi (isim ve ID'leri)
apps = {
    "Google Chrome": {"id": "Google.Chrome", "logo": "chrome.png"},
    "Mozilla Firefox": {"id": "Mozilla.Firefox", "logo": "mozilla.png"},
    "Adobe Photoshop": {"id": "Adobe.Photoshop", "logo": "photoshop.png"},
    "Audacity": {"id": "Audacity.Audacity", "logo": "audacity.png"},
    "VLC Media Player": {"id": "VideoLAN.VLC", "logo": "vlc.png"},
    "Spotify": {"id": "Spotify", "logo": "spotify.png"},
    "Microsoft Teams": {"id": "Microsoft.Teams", "logo": "teams.png"},
    "Zoom": {"id": "Zoom.Zoom", "logo": "zoom.png"},
    "Slack": {"id": "SlackTechnologies.Slack", "logo": "slack.png"},
    "GIMP": {"id": "GIMP.GIMP", "logo": "gimp.png"},
    "OBS Studio": {"id": "OBSProject.OBSStudio", "logo": "obs.png"},
    "FileZilla": {"id": "FileZilla.FileZilla", "logo": "filezilla.png"},
    "WinRAR": {"id": "RARLab.WinRAR", "logo": "winrar.png"},
    "7-Zip": {"id": "7zip.7zip", "logo": "7zip.png"},
    "Discord": {"id": "Discord.Discord", "logo": "discord.png"},
    "Adobe Acrobat Reader": {"id": "Adobe.AcrobatReader", "logo": "acrobat.png"},
    "WhatsApp": {"id": "WhatsApp.WhatsApp", "logo": "whatsapp.png"},
    "Notepad++": {"id": "NotepadPlusPlus.NotepadPlusPlus", "logo": "notepad.png"},
    "Visual Studio Code": {"id": "Microsoft.VisualStudioCode", "logo": "vscode.png"},
    "Steam": {"id": "Valve.Steam", "logo": "steam.png"},
    "EverNote": {"id": "evernote.evernote" , "logo": "evernote.png"},
    "Teamviewer" : {"id": "teamviewer.teamviewer" , "logo":"teamviewer.png"},
}

APP_ALIASES = {
    "Google Chrome": ["google chrome", "google.chrome.exe"],
    "Mozilla Firefox": ["mozilla firefox", "firefox"],
    "Adobe Photoshop": ["adobe photoshop", "photoshop", "phsp_"],
    "Spotify": ["spotify", "spotifymusic"],
    "WhatsApp": ["whatsapp", "whatsappdesktop", "5319275a.whatsappdesktop"],
    "Visual Studio Code": ["visual studio code", "vscode"],
    "Teamviewer": ["teamviewer", "team viewer"],
}

# İkon önbelleği
icon_cache = {}
scan_lock = threading.Lock()
scan_cache = {"timestamp": 0.0, "installed": set()}
registry_cache = {"timestamp": 0.0, "names": []}
SCAN_CACHE_TTL_SEC = 12
REGISTRY_CACHE_TTL_SEC = 180

def get_icon(app_name):
    if app_name not in icon_cache:
        logo_path = os.path.join(os.path.dirname(__file__), "icons", apps[app_name]["logo"])
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((64, 64), Image.LANCZOS)
            icon_cache[app_name] = CTkImage(light_image=img, dark_image=img, size=(64, 64))
    return icon_cache.get(app_name)

# Ana Frame
main_frame = ctk.CTkFrame(app)
main_frame.pack(pady=10, fill="both", expand=True)

# Sol ve sağ çerçeve (Yüklü ve Yüklü Olmayanlar)
installed_frame = ctk.CTkFrame(main_frame)
installed_frame.pack(side="left", padx=10, fill="both", expand=True)

not_installed_frame = ctk.CTkFrame(main_frame)
not_installed_frame.pack(side="right", padx=10, fill="both", expand=True)

# Başlıklar
installed_label = ctk.CTkLabel(installed_frame, text="Yüklü Uygulamalar", font=("Helvetica", 14))
installed_label.pack(pady=5)

not_installed_label = ctk.CTkLabel(not_installed_frame, text="Yüklü Olmayan Uygulamalar", font=("Helvetica", 14))
not_installed_label.pack(pady=5)

# İkonları tutacak Frame'ler
installed_icons_frame = ctk.CTkFrame(installed_frame)
installed_icons_frame.pack(pady=5, fill="both", expand=True)

not_installed_icons_frame = ctk.CTkFrame(not_installed_frame)
not_installed_icons_frame.pack(pady=5, fill="both", expand=True)

# İkonları ekleme fonksiyonu
def add_icons(app_list, container):
    max_rows = 3  # Maksimum satır sayısı
    max_columns = 4  # Maksimum sütun sayısı
    total_icons = len(app_list)

    # İkon boyutunu hesapla
    icon_size = 64  # Varsayılan ikon boyutu
    if total_icons > max_rows * max_columns:
        icon_size = int(64 * (max_rows * max_columns) / total_icons)

    row, col = 0, 0
    for app in app_list:
        if app in apps:
            logo_path = os.path.join(os.path.dirname(__file__), "icons", apps[app]["logo"])
            if os.path.exists(logo_path):
                # İkonu yeniden boyutlandır
                img = Image.open(logo_path).resize((icon_size, icon_size), Image.LANCZOS)
                resized_icon = ctk.CTkImage(light_image=img, dark_image=img, size=(icon_size, icon_size))

                label = ctk.CTkLabel(container, image=resized_icon, text="", width=icon_size, height=icon_size)
                label.grid(row=row, column=col, padx=5, pady=5)

                col += 1
                if col >= max_columns:
                    col = 0
                    row += 1

def render_installed_apps(installed_apps):
    # UI güncellemeleri sadece ana thread'de yapılmalı
    for widget in installed_icons_frame.winfo_children():
        widget.destroy()
    for widget in not_installed_icons_frame.winfo_children():
        widget.destroy()

    not_installed_apps = [app for app in apps.keys() if app not in installed_apps]
    add_icons(installed_apps, installed_icons_frame)
    add_icons(not_installed_apps, not_installed_icons_frame)

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
                            display_name = winreg.QueryValueEx(sk, 'DisplayName')[0]
                            names.append(display_name)
                        except Exception:
                            pass
                except Exception:
                    continue
    except Exception:
        pass
    return names

def get_registry_display_names(use_cache=True):
    if winreg is None:
        return []

    now = time.time()
    if use_cache and now - registry_cache["timestamp"] < REGISTRY_CACHE_TTL_SEC:
        return list(registry_cache["names"])

    found_names = []
    found_names += scan_registry_uninstall(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    found_names += scan_registry_uninstall(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    found_names += scan_registry_uninstall(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

    registry_cache["timestamp"] = now
    registry_cache["names"] = list(found_names)
    return found_names

def get_app_aliases(app_name, app_id):
    app_id_lower = app_id.lower()
    aliases = {
        app_name.lower(),
        app_id_lower,
        app_id_lower.replace(".exe", ""),
        app_id_lower.split(".")[-1]
    }
    for alias in APP_ALIASES.get(app_name, []):
        aliases.add(alias.lower())
    return [a for a in aliases if a]

def contains_any_alias(text_value, aliases):
    if not text_value:
        return False
    text_lower = text_value.lower()
    return any(alias in text_lower for alias in aliases)

def is_app_installed_via_winget(app_id):
    winget_path = shutil.which("winget")
    if winget_path is None:
        return False
    try:
        result = subprocess.run(
            [winget_path, "list", "--id", app_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = (result.stdout or "").lower()
        return app_id.lower() in output
    except Exception:
        return False

# Yüklü uygulamaları arka planda tarama fonksiyonu
def get_installed_apps(force_refresh=False):
    if not scan_lock.acquire(blocking=False):
        return

    installed_apps = set()
    try:
        now = time.time()
        if (not force_refresh) and (now - scan_cache["timestamp"] < SCAN_CACHE_TTL_SEC):
            cached = set(scan_cache["installed"])
            app.after(0, lambda apps_snapshot=cached: render_installed_apps(apps_snapshot))
            app.after(0, lambda: status_detail_label.configure(text="Tarama önbellekten yüklendi."))
            app.after(0, lambda: status_meta_label.configure(text="Hızlı tarama modu: Son sonuç kullanıldı."))
            return

        winget_path = shutil.which("winget")
        winget_full_output = ""
        if winget_path:
            try:
                winget_list = subprocess.run(
                    [winget_path, "list"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                winget_full_output = (winget_list.stdout or "").lower()
            except Exception:
                winget_full_output = ""

        unresolved_apps = []

        for app_name, app_info in apps.items():
            app_id = app_info["id"]
            aliases = get_app_aliases(app_name, app_id)
            if winget_full_output and contains_any_alias(winget_full_output, aliases):
                installed_apps.add(app_name)
                continue

            unresolved_apps.append((app_name, aliases))

        if unresolved_apps and winreg is not None:
            registry_names = get_registry_display_names(use_cache=True)
            registry_blob = "\n".join(registry_names).lower()
            for app_name, aliases in unresolved_apps:
                if contains_any_alias(registry_blob, aliases):
                    installed_apps.add(app_name)

        if winget_path is None and winreg is None:
            app.after(0, lambda: status_label.configure(text="winget ve winreg erişimi yok; tarama yapılamıyor."))
            return

        scan_cache["timestamp"] = time.time()
        scan_cache["installed"] = set(installed_apps)

        app.after(0, lambda apps_snapshot=set(installed_apps): render_installed_apps(apps_snapshot))
        app.after(0, lambda: status_detail_label.configure(text="Tarama tamamlandı."))
        app.after(0, lambda: status_meta_label.configure(text="Hızlı tarama: winget tek çağrı + seçici registry kontrolü."))
    except Exception as e:
        app.after(0, lambda: status_label.configure(text=f"Tarama sırasında hata: {e}"))
        print(f"Error while scanning installed apps: {e}")
    finally:
        scan_lock.release()

# Yüklü uygulamaları kontrol etme fonksiyonu (Thread ile)
def threaded_get_installed_apps(force_refresh=False):
    threading.Thread(target=get_installed_apps, args=(force_refresh,), daemon=True).start()

def is_app_installed(app_name, app_id):
    aliases = get_app_aliases(app_name, app_id)
    winget_path = shutil.which("winget")

    if winget_path:
        try:
            result = subprocess.run(
                [winget_path, "list", "--id", app_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = (result.stdout or "").lower()
            if contains_any_alias(output, aliases):
                return True
        except Exception:
            pass

        try:
            all_result = subprocess.run(
                [winget_path, "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            all_output = (all_result.stdout or "").lower()
            if contains_any_alias(all_output, aliases):
                return True
        except Exception:
            pass

    registry_blob = "\n".join(get_registry_display_names(use_cache=False)).lower()
    return contains_any_alias(registry_blob, aliases)

def run_winget_with_live_progress(cmd, selected_app, action_text):
    full_output = []

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        encoding=None,
        errors="replace"
    )

    ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    percent_re = re.compile(r"(\d{1,3})\s*%")
    size_re = re.compile(r"(\d+(?:[\.,]\d+)?)\s*(KB|MB|GB)\s*/\s*(\d+(?:[\.,]\d+)?)\s*(KB|MB|GB)", re.IGNORECASE)

    start_time = time.time()
    last_progress = 0.0
    saw_real_progress = False

    app.after(0, lambda: progress_bar.set(0))

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
        minutes = elapsed // 60
        seconds = elapsed % 60
        elapsed_text = f"{minutes:02d}:{seconds:02d}"

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
            app.after(0, lambda v=progress_value: progress_bar.set(v))
        elif size_match:
            downloaded = f"{size_match.group(1)} {size_match.group(2).upper()}"
            total = f"{size_match.group(3)} {size_match.group(4).upper()}"
            detail_text = f"{selected_app} {action_text}... ({downloaded} / {total})"
            if last_progress < 0.95:
                last_progress = min(last_progress + 0.02, 0.95)
                app.after(0, lambda v=last_progress: progress_bar.set(v))
        else:
            if last_progress < 0.9:
                last_progress = min(last_progress + 0.01, 0.9)
                app.after(0, lambda v=last_progress: progress_bar.set(v))

        app.after(0, lambda d=detail_text: status_detail_label.configure(text=d))
        app.after(0, lambda m=f"Süre: {elapsed_text} | Son çıktı: {clean_line[:110]}": status_meta_label.configure(text=m))

    # winget genelde ayni satiri \r ile guncelledigi icin karakter bazli ayrisim yap
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
        app.after(0, lambda: status_meta_label.configure(text="Canli ilerleme verisi sinirli geldi; kurucu pencere asamasinda olabilir."))

    return process.returncode, "\n".join(full_output)

# Tarama butonunu güncelle
scan_button = ctk.CTkButton(app, text="Yüklü Uygulamaları Tara", command=threaded_get_installed_apps)
scan_button.pack(pady=10)

# Durum paneli
status_panel = ctk.CTkFrame(app, corner_radius=10, fg_color=("#1f2430", "#1f2430"))
status_panel.pack(fill="x", padx=20, pady=4)
status_panel.pack_propagate(False)
status_panel.configure(height=82)

status_label = ctk.CTkLabel(status_panel, text="", font=("Helvetica", 12, "bold"), anchor="w")
status_label.pack(fill="x", padx=10, pady=(5, 1))

status_detail_label = ctk.CTkLabel(status_panel, text="Hazır", font=("Helvetica", 11), anchor="w")
status_detail_label.pack(fill="x", padx=10, pady=(0, 1))

# Progress bar
progress_bar = ctk.CTkProgressBar(status_panel, width=560)
progress_bar.set(0)
progress_bar.pack(fill="x", padx=10, pady=(2, 4))

status_meta_label = ctk.CTkLabel(status_panel, text="", font=("Helvetica", 11), anchor="w", text_color="gray70")
# Kompakt gorunum icin meta satiri gizli tutulur; yine de metin guncellenebilir.

# Yükleme ve kaldırma fonksiyonları
def manage_app(action):
    selected_app = app_list.get()
    if selected_app in apps:
        app_id = apps[selected_app]["id"]
        status_label.configure(text=f"{selected_app} {'yükleniyor' if action == 'install' else 'kaldırılıyor'}...")
        status_detail_label.configure(text=f"{selected_app} için işlem başlatıldı.")
        status_meta_label.configure(text="Komut hazırlanıyor...")
        progress_bar.set(0)

        def process():
            winget_path = shutil.which("winget")
            if winget_path is None:
                app.after(0, lambda: status_label.configure(text="winget bulunamadı. Uygulama yükleme yapılamıyor."))
                app.after(0, lambda: status_detail_label.configure(text="İşlem başlatılamadı."))
                app.after(0, lambda: progress_bar.set(0))
                return

            currently_installed = is_app_installed(selected_app, app_id)
            currently_installed_via_winget = is_app_installed_via_winget(app_id)
            if action == "uninstall" and not currently_installed:
                app.after(0, lambda: progress_bar.set(0))
                app.after(0, lambda: status_label.configure(text=f"{selected_app} sistemde kurulu görünmüyor."))
                app.after(0, lambda: status_detail_label.configure(text="Kaldırma adımı atlandı."))
                app.after(0, lambda: threaded_get_installed_apps(force_refresh=True))
                return
            if action == "uninstall" and currently_installed and not currently_installed_via_winget:
                app.after(0, lambda: progress_bar.set(0))
                app.after(0, lambda: status_label.configure(text=f"{selected_app} kurulu, ancak winget ile yönetilen paket bulunamadı."))
                app.after(0, lambda: status_detail_label.configure(text="Bu kurulum uygulamanin kendi kaldiricisi ile silinmeli."))
                app.after(0, lambda: threaded_get_installed_apps(force_refresh=True))
                return

            cmd = [winget_path, action, "--id", app_id, "--exact"]
            if action == "install":
                cmd += ["--accept-package-agreements", "--accept-source-agreements"]

            action_text = "yükleniyor" if action == "install" else "kaldırılıyor"
            return_code, full_output = run_winget_with_live_progress(cmd, selected_app, action_text)

            output_text = (full_output or "").lower()
            is_cancelled = any(token in output_text for token in [
                "cancel",
                "canceled",
                "cancelled",
                "iptal",
                "1602"
            ])

            installed_now = is_app_installed(selected_app, app_id)

            if action == "install":
                if installed_now:
                    app.after(0, lambda: progress_bar.set(1))
                    app.after(0, lambda: status_label.configure(text=f"{selected_app} yüklendi!"))
                    app.after(0, lambda: status_detail_label.configure(text="Kurulum doğrulandı."))
                elif is_cancelled:
                    app.after(0, lambda: progress_bar.set(0))
                    app.after(0, lambda: status_label.configure(text=f"{selected_app} yükleme iptal edildi."))
                    app.after(0, lambda: status_detail_label.configure(text="Kullanıcı kurulumu iptal etti."))
                else:
                    app.after(0, lambda: progress_bar.set(0))
                    if return_code != 0:
                        app.after(0, lambda: status_label.configure(text=f"{selected_app} yüklenemedi. (Kod: {return_code})"))
                        app.after(0, lambda: status_detail_label.configure(text="Kurulum komutu hata ile sonlandı."))
                    else:
                        app.after(0, lambda: status_label.configure(text=f"{selected_app} yüklenemedi veya kurulum tamamlanmadı."))
                        app.after(0, lambda: status_detail_label.configure(text="Kurulum sonrası doğrulama başarısız."))
            else:
                if not installed_now:
                    app.after(0, lambda: progress_bar.set(1))
                    app.after(0, lambda: status_label.configure(text=f"{selected_app} kaldırıldı!"))
                    app.after(0, lambda: status_detail_label.configure(text="Kaldırma doğrulandı."))
                elif is_cancelled:
                    app.after(0, lambda: progress_bar.set(0))
                    app.after(0, lambda: status_label.configure(text=f"{selected_app} kaldırma iptal edildi."))
                    app.after(0, lambda: status_detail_label.configure(text="Kullanıcı kaldırma adımını iptal etti."))
                else:
                    app.after(0, lambda: progress_bar.set(0))
                    if "no installed package found" in output_text:
                        app.after(0, lambda: status_label.configure(text=f"{selected_app} winget ile kurulu bulunamadı."))
                        app.after(0, lambda: status_detail_label.configure(text="Paket listede görünmüyor."))
                    else:
                        if return_code != 0:
                            app.after(0, lambda: status_label.configure(text=f"{selected_app} kaldırılamadı. (Kod: {return_code})"))
                            app.after(0, lambda: status_detail_label.configure(text="Kaldırma komutu hata verdi."))
                        else:
                            app.after(0, lambda: status_label.configure(text=f"{selected_app} kaldırılamadı veya kaldırma tamamlanmadı."))
                            app.after(0, lambda: status_detail_label.configure(text="Kaldırma sonrası doğrulama başarısız."))

            app.after(0, lambda: threaded_get_installed_apps(force_refresh=True))

        threading.Thread(target=process, daemon=True).start()

# Uygulama güncelleme fonksiyonu
def update_app():
    selected_app = app_list.get()
    if selected_app in apps:
        app_id = apps[selected_app]["id"]
        status_label.configure(text=f"{selected_app} güncelleniyor...")
        status_detail_label.configure(text=f"{selected_app} için güncelleme başlatıldı.")
        status_meta_label.configure(text="Komut hazırlanıyor...")
        progress_bar.set(0)

        def process():
            winget_path = shutil.which("winget")
            if winget_path is None:
                app.after(0, lambda: status_label.configure(text="winget bulunamadı. Güncelleme yapılamıyor."))
                app.after(0, lambda: status_detail_label.configure(text="Güncelleme başlatılamadı."))
                app.after(0, lambda: progress_bar.set(0))
                return

            cmd = [winget_path, "upgrade", "--id", app_id, "--exact", "--accept-package-agreements", "--accept-source-agreements"]
            return_code, full_output = run_winget_with_live_progress(cmd, selected_app, "güncelleniyor")

            output_text = (full_output or "").lower()
            if return_code == 0:
                app.after(0, lambda: progress_bar.set(1))
                app.after(0, lambda: status_label.configure(text=f"{selected_app} güncellendi!"))
                app.after(0, lambda: status_detail_label.configure(text="Güncelleme doğrulandı."))
            elif any(token in output_text for token in ["cancel", "canceled", "cancelled", "iptal", "1602"]):
                app.after(0, lambda: progress_bar.set(0))
                app.after(0, lambda: status_label.configure(text=f"{selected_app} güncelleme iptal edildi."))
                app.after(0, lambda: status_detail_label.configure(text="Kullanıcı güncellemeyi iptal etti."))
            else:
                app.after(0, lambda: progress_bar.set(0))
                app.after(0, lambda: status_label.configure(text=f"{selected_app} güncellenemedi. (Kod: {return_code})"))
                app.after(0, lambda: status_detail_label.configure(text="Güncelleme komutu hata ile sonlandı."))
            app.after(0, lambda: threaded_get_installed_apps(force_refresh=True))

        threading.Thread(target=process, daemon=True).start()

# Uygulama Listesi için ComboBox
app_list = ctk.CTkComboBox(app, values=list(apps.keys()))
app_list.pack(pady=10)

# Yükle, Kaldır ve Güncelle Butonları (yan yana)
buttons_frame = ctk.CTkFrame(app, fg_color="transparent")
buttons_frame.pack(pady=6)

install_button = ctk.CTkButton(buttons_frame, text="Yükle", width=150, command=lambda: manage_app("install"))
install_button.pack(side="left", padx=6)

uninstall_button = ctk.CTkButton(buttons_frame, text="Kaldır", width=150, command=lambda: manage_app("uninstall"))
uninstall_button.pack(side="left", padx=6)

update_button = ctk.CTkButton(buttons_frame, text="Güncelle", width=150, command=update_app)
update_button.pack(side="left", padx=6)

# Hareket eden imza için fonksiyon
def animate_signature():
    global signature_text
    signature_text = signature_text[1:] + signature_text[0]
    signature_label.configure(text=signature_text)
    app.after(300, animate_signature)  # Yenileme hızını artır

# İmza metni
signature_text = "  Designed by Serhat-Can  "  # İmzanız

# İmza etiketi için çerçeve (arka plan efekti için)
signature_frame = ctk.CTkFrame(
    app,
    fg_color=("gray20", "gray10"),  # Degrade arka plan
    corner_radius=10
)
signature_frame.pack(side="bottom", pady=10, fill="x", padx=20)

# İmza etiketi
signature_label = ctk.CTkLabel(
    signature_frame,
    text=signature_text,
    font=("Courier New", 14, "bold"),  # Daha modern bir yazı tipi
    text_color="#FFD700"  # Altın sarısı renk
)
signature_label.pack(pady=5)

# Animasyonu başlat
animate_signature()

# Başlangıçta dil ve tema ayarlarını yükle
lang_texts = load_language(settings.get("language", "Türkçe"))
update_language(settings["language"])

# Tema adlarını başlangıç diline göre güncelle
if settings["language"] == "Türkçe":
    theme_menu.configure(values=["Koyu", "Açık"])
    theme_menu.set("Koyu" if settings["Theme"] == "Dark" else "Açık")
elif settings["language"] == "English":
    theme_menu.configure(values=["Dark", "Light"])
    theme_menu.set("Dark" if settings["Theme"] == "Dark" else "Light")
elif settings["language"] == "Русский":
    theme_menu.configure(values=["Тёмная", "Светлая"])
    theme_menu.set("Тёмная" if settings["Theme"] == "Dark" else "Светлая")
elif settings["language"] == "Deutsch":
    theme_menu.configure(values=["Dunkel", "Hell"])
    theme_menu.set("Dunkel" if settings["Theme"] == "Dark" else "Hell")
elif settings["language"] == "中文":
    theme_menu.configure(values=["深色", "浅色"])
    theme_menu.set("深色" if settings["Theme"] == "Dark" else "浅色")
elif settings["language"] == "Español":
    theme_menu.configure(values=["Oscuro", "Claro"])
    theme_menu.set("Oscuro" if settings["Theme"] == "Dark" else "Claro")
elif settings["language"] == "العربية":
    theme_menu.configure(values=["داكن", "فاتح"])
    theme_menu.set("داكن" if settings["Theme"] == "Dark" else "فاتح")

# Uygulama başlat
ctk.set_appearance_mode(settings["Theme"])
app.mainloop()
