#define MyAppName "SCAN"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Serhat Can"
#define MyAppExeName "SCAN.exe"

[Setup]
AppId={{A1F6D2B0-9E2A-4E50-BB71-123456789999}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SCAN
DefaultGroupName=SCAN
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=SCAN-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\SCAN.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü simgesi oluştur"; Flags: unchecked

[Files]
Source: "dist\SCAN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SCAN"; Filename: "{app}\SCAN.exe"
Name: "{group}\SCAN Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SCAN"; Filename: "{app}\SCAN.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SCAN.exe"; Description: "SCAN uygulamasını başlat"; Flags: nowait postinstall skipifsilent