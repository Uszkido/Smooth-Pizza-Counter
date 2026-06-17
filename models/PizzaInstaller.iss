; ─────────────────────────────────────────────────────────────────────────────
; Pizza & Ice Cream Club — AI VMS  v3.0  (Web-Based Dashboard Edition)
; Installer Script (Inno Setup 6)
; Developed by Vexel Innovations
; ─────────────────────────────────────────────────────────────────────────────

[Setup]
AppName=Pizza & Ice Cream Club AI VMS
AppVersion=3.0
AppPublisher=Vexel Innovations
AppPublisherURL=https://vexelinnovations.com
AppSupportURL=https://vexelinnovations.com
AppUpdatesURL=https://vexelinnovations.com
AppComments=Web-Based Dashboard with System-Tray Launcher — Powered by AI

; Installation directory
DefaultDirName={pf}\VexelInnovations\PizzaVMS
DefaultGroupName=Vexel Innovations
AllowNoIcons=yes

; Output
OutputDir=dist_Installer
OutputBaseFilename=PizzaVMS_Setup_v3

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; UI
WizardStyle=modern
UninstallDisplayIcon={app}\PizzaVMS.exe
UninstallDisplayName=Pizza & Ice Cream Club AI VMS

; Requirements
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Give the user a choice at install time
Name: "desktopicon";    Description: "Create a &Desktop shortcut";    GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startupicon";    Description: "Launch VMS automatically at &Windows startup"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Pack everything from the NEW PyInstaller output folder (dist_FINAL\PizzaVMS)
Source: "dist_FINAL\PizzaVMS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\Pizza & Ice Cream VMS";  Filename: "{app}\PizzaVMS.exe"; Comment: "AI Pizza Counter — Web Dashboard"
Name: "{group}\Uninstall Pizza VMS";    Filename: "{uninstallexe}"

; Desktop (only if task selected)
Name: "{commondesktop}\Pizza & Ice Cream VMS"; Filename: "{app}\PizzaVMS.exe"; Comment: "AI Pizza Counter — Web Dashboard"; Tasks: desktopicon

; Windows Startup folder (only if task selected)
Name: "{userstartup}\Pizza & Ice Cream VMS";   Filename: "{app}\PizzaVMS.exe"; Tasks: startupicon

[Run]
; Optionally launch the app immediately after install
Filename: "{app}\PizzaVMS.exe"; Description: "Launch AI VMS now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill the process before uninstalling
Filename: "taskkill"; Parameters: "/f /im PizzaVMS.exe"; Flags: runhidden

[Code]
var ResultCode: Integer;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    Exec('taskkill', '/f /im PizzaVMS.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
