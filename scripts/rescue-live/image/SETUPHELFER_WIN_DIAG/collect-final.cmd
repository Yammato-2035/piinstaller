@echo off
REM Final flush of live capture — PI-RS-ASUS-AUTOCAPTURE-BIOS-007
setlocal
set "SCRIPT_DIR=%~dp0"
set SETUPHELFER_WIN11_CAPTURE_ONCE=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%collect-win11-live-capture.ps1" -IntervalSec 1 -MaxMinutes 1 %*
exit /b %ERRORLEVEL%
