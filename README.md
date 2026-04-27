# SCAN - Winget GUI (CustomTkinter)

Windows için çok dilli, tema destekli, **winget** tabanlı uygulama tarayıcı ve yönetici.  
Yüklü ve yüklü olmayan uygulamaları ikonlarla gösterir; seçtiğiniz uygulamayı **Yükle / Kaldır / Güncelle** komutlarıyla tek tıkla yönetir.

![Screenshot](docs/screenshot.png)

## Özellikler

- Koyu/Açık tema desteği
- Çok dilli arayüz: Türkçe, English, Русский, Deutsch, 中文, Español, العربية
- Yüklü ve yüklü olmayan uygulamaları listeleme
- Seçili uygulama için yükleme, kaldırma ve güncelleme
- İkonlarla modern grid yerleşimi
- Kullanıcı profiline kaydedilen kişisel ayarlar
- GitHub kısayolu

> Çoklu dil metinleri `languages.json` içinde, ayarlar ise kullanıcı profilindeki uygulama klasöründe saklanır.

## Desteklenen Platform

- Windows 10/11
- `winget` kurulu sistem

## Kurulum

```bash
git clone https://github.com/<kullanici-adin>/SCAN.git
cd SCAN

python -m venv .venv

# PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python SCAN.py
```

## Sorumluluk Reddi

Bu yazılım `winget` üzerinden üçüncü parti yazılımlarda değişiklik yapar.
Yapılan işlemler kullanıcı sorumluluğundadır; üretim ortamında kullanmadan önce test edilmelidir.
