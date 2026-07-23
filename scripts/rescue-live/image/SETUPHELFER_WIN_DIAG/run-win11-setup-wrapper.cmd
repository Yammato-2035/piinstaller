@echo off
REM Setuphelfer controlled Windows Setup wrapper — PI-RS-ASUS-LAB-CONTROL-006
REM Starts live capture, then documents setup.exe invocation. No BitLocker mutation.
REM Do not invent unsupported setup flags. /noreboot only if explicitly enabled AND verified.
setlocal EnableExtensions

if "%SETUPHELFER_WIN11_RUN_ID%"=="" (
  echo [setuphelfer] ERROR: SETUPHELFER_WIN11_RUN_ID required ^(asus-win11-...^)
  exit /b 2
)
echo %SETUPHELFER_WIN11_RUN_ID% | findstr /I "norunid unknown" >nul
if not errorlevel 1 (
  echo [setuphelfer] ERROR: forbidden run_id
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "CAPTURE_PS1=%SCRIPT_DIR%collect-win11-live-capture.ps1"
set "SETUP_EXE=%SETUPHELFER_WIN11_SETUP_EXE%"
if "%SETUP_EXE%"=="" set "SETUP_EXE=D:\sources\setup.exe"

echo [setuphelfer] run_id=%SETUPHELFER_WIN11_RUN_ID%
echo [setuphelfer] starting live capture in background...
start "setuphelfer-live-capture" /MIN powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CAPTURE_PS1%" -RunId "%SETUPHELFER_WIN11_RUN_ID%" -IntervalSec 30

timeout /t 3 /nobreak >nul

set "EXTRA="
if /I "%SETUPHELFER_WIN11_NOREBOOT%"=="1" (
  echo [setuphelfer] NOTE: /noreboot requested — only if this setup.exe build supports it.
  set "EXTRA=/noreboot"
)

echo [setuphelfer] invoking: "%SETUP_EXE%" %EXTRA% %*
if not exist "%SETUP_EXE%" (
  echo [setuphelfer] ERROR: setup.exe not found at %SETUP_EXE%
  exit /b 3
)

"%SETUP_EXE%" %EXTRA% %*
set "EC=%ERRORLEVEL%"
echo [setuphelfer] setup exitcode=%EC%

set SETUPHELFER_WIN11_CAPTURE_ONCE=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CAPTURE_PS1%" -RunId "%SETUPHELFER_WIN11_RUN_ID%" -IntervalSec 1 -MaxMinutes 1
echo [setuphelfer] final capture flush attempted
exit /b %EC%
