' ═══════════════════════════════════════════════════════════
'  PizzaClub AI Server — Hidden Background Launcher
'  Launches WATCHDOG.bat completely invisibly.
'  No CMD window. No taskbar entry. Runs detached from all UIs.
'  Used by INSTALL_SERVICE.bat and can be double-clicked directly.
' ═══════════════════════════════════════════════════════════
Option Explicit

Dim WshShell, fso, strDir, strWatchdog

Set fso     = CreateObject("Scripting.FileSystemObject")
strDir      = fso.GetParentFolderName(WScript.ScriptFullName)
strWatchdog = strDir & "\WATCHDOG.bat"

If Not fso.FileExists(strWatchdog) Then
    MsgBox "WATCHDOG.bat not found at:" & vbCrLf & strWatchdog, vbCritical, "PizzaClub Launcher Error"
    WScript.Quit 1
End If

' Launch the watchdog completely hidden (0 = hidden window, False = don't wait)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """" & strWatchdog & """", 0, False

' Done — this VBS exits immediately; the watchdog runs independently
