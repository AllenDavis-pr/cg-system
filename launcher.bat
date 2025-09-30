@echo off
setlocal

REM Change directory to the folder of this batch file
cd /d "%~dp0"

REM -----------------------------
REM Step 1: Create a desktop shortcut
REM -----------------------------
set TARGET=%~dp0launcher.bat
set LINKNAME=CG Price Suggestor.lnk
set ICONFILE=%~dp0icon.ico

REM Try multiple desktop locations
set DESKTOP=%USERPROFILE%\Desktop
if not exist "%DESKTOP%" set DESKTOP=%USERPROFILE%\OneDrive\Desktop
if not exist "%DESKTOP%" set DESKTOP=%PUBLIC%\Desktop

REM Check if desktop folder exists
if not exist "%DESKTOP%" (
    echo Warning: Could not find Desktop folder. Shortcut not created.
    goto :skip_shortcut
)

REM Create the shortcut with custom icon
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%DESKTOP%\%LINKNAME%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%ICONFILE%'; $s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo Shortcut created successfully at: %DESKTOP%\%LINKNAME%
) else (
    echo Failed to create shortcut.
)

:skip_shortcut

REM -----------------------------
REM Step 2: Run your bundled Python launcher
REM -----------------------------
python\cgpython.exe desktop_launcher.py

endlocal