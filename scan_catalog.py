from __future__ import annotations

AppEntry = dict[str, str]


APPS: dict[str, AppEntry] = {
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
    "EverNote": {"id": "evernote.evernote", "logo": "evernote.png"},
    "Teamviewer": {"id": "teamviewer.teamviewer", "logo": "teamviewer.png"},
}


APP_ALIASES: dict[str, list[str]] = {
    "Google Chrome": ["google chrome", "google.chrome.exe"],
    "Mozilla Firefox": ["mozilla firefox", "firefox"],
    "Adobe Photoshop": ["adobe photoshop", "photoshop", "phsp_"],
    "Spotify": ["spotify", "spotifymusic"],
    "WhatsApp": ["whatsapp", "whatsappdesktop", "5319275a.whatsappdesktop"],
    "Visual Studio Code": ["visual studio code", "vscode"],
    "Teamviewer": ["teamviewer", "team viewer"],
}
