#define MyAppName "HomeWork Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TJ Sanders"
#define MyAppExeName "HomeWorkTracker.exe"
#define MyAppIconRel "_internal\icon\app-icon.ico"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppId={{A3F8C2D1-4E7B-4F2A-9C3D-1B5E8A7F2C4D}
DefaultDirName={localappdata}\HomeWorkTracker
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=HomeWorkTracker-Setup
SetupIconFile=icon\app-icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
DisableReadyPage=no
DisableFinishedPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\HomeWorkTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconRel}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconRel}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue

[Code]
procedure CreateConfigJson();
var
  ConfigPath: string;
  ConfigContent: string;
begin
  ConfigPath := ExpandConstant('{app}\config.json');
  if not FileExists(ConfigPath) then
  begin
    ConfigContent := '{"api_base": "http://127.0.0.1:8000", "on_top": false}';
    SaveStringToFile(ConfigPath, ConfigContent, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateConfigJson();
end;

[UninstallDelete]
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\tweaks.json"
Type: files; Name: "{app}\token.json"
Type: files; Name: "{app}\_internal\token.json"
Type: files; Name: "{app}\_internal\sync_map.json"
Type: files; Name: "{app}\_internal\static\_runtime.html"
