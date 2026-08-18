#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName "CamSend"
#define MyAppExeName "CamSend.exe"
#define MyProjectUrl "https://github.com/Peyman0117/CamSend"

[Setup]
AppId={{71176835-94F9-4554-A001-484C08C2A703}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=CamSend Project
AppPublisherURL=https://camsend.app
AppSupportURL={#MyProjectUrl}/issues
AppUpdatesURL={#MyProjectUrl}/releases
DefaultDirName={autopf}\CamSend
DefaultGroupName=CamSend
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\release
OutputBaseFilename=CamSend-Setup-{#MyAppVersion}
SetupIconFile=..\..\build\camsend.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
Uninstallable=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#MyAppVersion}.0
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\..\dist\CamSend\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CamSend"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\CamSend"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch CamSend"; Flags: nowait postinstall skipifsilent runasoriginaluser
