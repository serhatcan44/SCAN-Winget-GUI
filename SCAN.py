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
import lottiWiev 

# Tkinter ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Ana pencere oluştur
app = ctk.CTk()
app.geometry("800x700+{}+{}".format(int(app.winfo_screenwidth() / 2 - 350), int(app.winfo_screenheight() / 2 - 380)))
app.title("SCAN")
app.resizable(False, False)

# Programın logosunu ayarla
app.iconbitmap(r"c:\Users\canse\Desktop\UygulamaYükleme\app_icon.ico")  # Tam yol

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

# İkon önbelleği
icon_cache = {}

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

# Yüklü uygulamaları kontrol etme fonksiyonu
def get_installed_apps():
    # Önce mevcut ikonları temizle
    for widget in installed_icons_frame.winfo_children():
        widget.destroy()
    for widget in not_installed_icons_frame.winfo_children():
        widget.destroy()

    installed_apps = set()
    try:
        # winget komutunu çalıştır ve çıktısını al
        result = subprocess.run(
            ["winget", "list"],
            stdout=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Konsolun açılmasını engeller
        )
        if result.returncode == 0:
            winget_output = result.stdout.lower()

            # Uygulama isimlerini kontrol et
            for app_name in apps.keys():
                if app_name.lower() in winget_output:
                    installed_apps.add(app_name)

    except subprocess.CalledProcessError as e:
        print(f"Error while running winget: {e}")

    # Yüklü olmayan uygulamaları belirle
    not_installed_apps = [app for app in apps.keys() if app not in installed_apps]

    # İkonları ekle
    add_icons(installed_apps, installed_icons_frame)
    add_icons(not_installed_apps, not_installed_icons_frame)

# Yüklü uygulamaları kontrol etme fonksiyonu (Thread ile)
def threaded_get_installed_apps():
    threading.Thread(target=get_installed_apps, daemon=True).start()

# Tarama butonunu güncelle
scan_button = ctk.CTkButton(app, text="Yüklü Uygulamaları Tara", command=threaded_get_installed_apps)
scan_button.pack(pady=10)

# Durum etiketi
status_label = ctk.CTkLabel(app, text="", font=("Helvetica", 12))
status_label.pack(pady=5)

# Progress bar
progress_bar = ctk.CTkProgressBar(app, width=400)
progress_bar.set(0)
progress_bar.pack(pady=5)

# Yükleme ve kaldırma fonksiyonları
def manage_app(action):
    selected_app = app_list.get()
    if selected_app in apps:
        app_id = apps[selected_app]["id"]
        status_label.configure(text=f"{selected_app} {'yükleniyor' if action == 'install' else 'kaldırılıyor'}...")
        progress_bar.set(0.5)

        def process():
            result = subprocess.run(["winget", action, app_id, "--silent"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                progress_bar.set(1)
                status_label.configure(text=f"{selected_app} {'yüklendi' if action == 'install' else 'kaldırıldı'}!")
            else:
                progress_bar.set(0)
                status_label.configure(text=f"{selected_app} {'yüklenemedi' if action == 'install' else 'kaldırılamadı'}! Hata: {result.stderr.decode('utf-8')}")
            get_installed_apps()

        threading.Thread(target=process, daemon=True).start()

# Uygulama güncelleme fonksiyonu
def update_app():
    selected_app = app_list.get()
    if selected_app in apps:
        app_id = apps[selected_app]["id"]
        status_label.configure(text=f"{selected_app} güncelleniyor...")
        progress_bar.set(0.5)

        def process():
            result = subprocess.run(["winget", "upgrade", app_id, "--silent"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                progress_bar.set(1)
                status_label.configure(text=f"{selected_app} güncellendi!")
            else:
                progress_bar.set(0)
                status_label.configure(text=f"{selected_app} güncellenemedi! Hata: {result.stderr.decode('utf-8')}")
            get_installed_apps()

        threading.Thread(target=process, daemon=True).start()

# Uygulama Listesi için ComboBox
app_list = ctk.CTkComboBox(app, values=list(apps.keys()))
app_list.pack(pady=10)

# Yükle, Kaldır ve Güncelle Butonları
install_button = ctk.CTkButton(app, text="Yükle", command=lambda: manage_app("install"))
install_button.pack(pady=5)

uninstall_button = ctk.CTkButton(app, text="Kaldır", command=lambda: manage_app("uninstall"))
uninstall_button.pack(pady=5)

update_button = ctk.CTkButton(app, text="Güncelle", command=update_app)
update_button.pack(pady=5)

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
