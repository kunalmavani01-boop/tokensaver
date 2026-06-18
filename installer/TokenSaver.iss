[Setup]
AppName=TokenSaver
AppVersion=1.0.0
DefaultDirName={autopf}\TokenSaver
DefaultGroupName=TokenSaver
OutputDir=..\dist
OutputBaseFilename=TokenSaver-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist\TokenSaver.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TokenSaver"; Filename: "{app}\TokenSaver.exe"
Name: "{commondesktop}\TokenSaver"; Filename: "{app}\TokenSaver.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\TokenSaver.exe"; Description: "Launch TokenSaver"; Flags: nowait postinstall skipifsilent
