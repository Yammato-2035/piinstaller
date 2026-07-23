@echo off
REM Auto-start Windows live collector — PI-RS-ASUS-AUTOCAPTURE-BIOS-007
REM No manual Run-ID required. SETUP_LOGS by label/TAG only. No BitLocker mutation.
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-collector.ps1" %*
exit /b %ERRORLEVEL%
