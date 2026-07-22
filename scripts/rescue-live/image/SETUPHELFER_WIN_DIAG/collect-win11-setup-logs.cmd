@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM Setuphelfer WinPE collector — read-only copy of Windows Setup logs.
REM No partitioning. No online disk. No registry edits. No credentials.

set "SCRIPT_DIR=%~dp0"
set "TAG_NAME=SETUP_LOGS.TAG"
set "OUT_ROOT="
set "STAMP="
set "RUN_ID="

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%I"
if "%STAMP%"=="" set "STAMP=unknown"
for /f %%I in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString(\"N\").Substring(0,8)"') do set "RUN_ID=%%I"
if "%RUN_ID%"=="" set "RUN_ID=norunid"

echo [setuphelfer] Searching for SETUP_LOGS destination...
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\%TAG_NAME%" (
    set "OUT_ROOT=%%D:\setuphelfer-win11-logs"
    goto :found_out
  )
)

REM Match volume label SETUP_LOGS via wmic if available
for /f "skip=1 tokens=1,2*" %%A in ('wmic volume get DriveLetter^,Label 2^>nul') do (
  if /I "%%B"=="SETUP_LOGS" if not "%%A"=="" (
    set "OUT_ROOT=%%A\setuphelfer-win11-logs"
    goto :found_out
  )
)

REM Fallback: mountvol listing (letters vary)
for /f "tokens=1,*" %%A in ('mountvol 2^>nul') do (
  rem informational only
)

:found_out
if "%OUT_ROOT%"=="" (
  echo [setuphelfer] ERROR: SETUP_LOGS.TAG / label SETUP_LOGS not found.
  echo Place the rescue SETUP_LOGS partition or copy SETUP_LOGS.TAG to the target volume.
  exit /b 2
)

set "RUN_DIR=%OUT_ROOT%\%STAMP%-%RUN_ID%"
mkdir "%RUN_DIR%" 2>nul
echo [setuphelfer] Output: %RUN_DIR%

echo setuphelfer_win_diag=1> "%RUN_DIR%\collector_meta.txt"
echo stamp=%STAMP%>> "%RUN_DIR%\collector_meta.txt"
echo run_id=%RUN_ID%>> "%RUN_DIR%\collector_meta.txt"
echo computername=%COMPUTERNAME%>> "%RUN_DIR%\collector_meta.txt"
echo date=%DATE% %TIME%>> "%RUN_DIR%\collector_meta.txt"

REM Boot / time info
echo. > "%RUN_DIR%\boot_time.txt"
echo DATE=%DATE%>> "%RUN_DIR%\boot_time.txt"
echo TIME=%TIME%>> "%RUN_DIR%\boot_time.txt"
bcdedit /enum all > "%RUN_DIR%\bcdedit_enum_all.txt" 2>&1
mountvol > "%RUN_DIR%\mountvol.txt" 2>&1

REM Inventory all drive roots (letters vary)
echo. > "%RUN_DIR%\drive_roots.txt"
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\" echo %%D:>> "%RUN_DIR%\drive_roots.txt"
)

REM Prefer PowerShell disk inventory when available
if exist "%SCRIPT_DIR%collect-win11-disk-info.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%collect-win11-disk-info.ps1" -OutDir "%RUN_DIR%"
) else (
  call "%SCRIPT_DIR%collect-win11-disk-info.cmd" "%RUN_DIR%"
)

if exist "%SCRIPT_DIR%collect-win11-boot-info.cmd" (
  call "%SCRIPT_DIR%collect-win11-boot-info.cmd" "%RUN_DIR%"
)

REM Prefer PS1 log collector body when available
if exist "%SCRIPT_DIR%collect-win11-setup-logs.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%collect-win11-setup-logs.ps1" -OutDir "%RUN_DIR%"
  echo [setuphelfer] Log collection finished via PS1. Review %RUN_DIR%
  exit /b 0
)

call :copy_tree "X:\Windows\Panther" "%RUN_DIR%\from_X_Windows_Panther"
call :copy_tree "X:\$WINDOWS.~BT\Sources\Panther" "%RUN_DIR%\from_X_WINDOWS_BT_Panther"
call :copy_tree "X:\Windows\System32\LogFiles" "%RUN_DIR%\from_X_LogFiles"
call :copy_tree "X:\Windows\Logs\DISM" "%RUN_DIR%\from_X_DISM"
call :copy_tree "X:\Windows\Logs\CBS" "%RUN_DIR%\from_X_CBS"

for %%D in (C D E F G H I J K L M N O P Q R S T U V W Y Z) do (
  call :copy_tree "%%D:\$WINDOWS.~BT\Sources\Panther" "%RUN_DIR%\from_%%D_WINDOWS_BT_Panther"
  call :copy_tree "%%D:\$WINDOWS.~BT\Sources\Rollback" "%RUN_DIR%\from_%%D_WINDOWS_BT_Rollback"
  call :copy_tree "%%D:\Windows\Panther" "%RUN_DIR%\from_%%D_Windows_Panther"
  call :copy_tree "%%D:\Windows\Panther\NewOS" "%RUN_DIR%\from_%%D_Windows_Panther_NewOS"
  call :copy_tree "%%D:\Windows\Panther\UnattendGC" "%RUN_DIR%\from_%%D_Windows_Panther_UnattendGC"
  call :copy_tree "%%D:\Windows\Logs\DISM" "%RUN_DIR%\from_%%D_DISM"
  call :copy_tree "%%D:\Windows\Logs\CBS" "%RUN_DIR%\from_%%D_CBS"
  call :copy_tree "%%D:\Windows\Logs\MoSetup" "%RUN_DIR%\from_%%D_MoSetup"
  call :copy_tree "%%D:\Windows\Logs\Setup" "%RUN_DIR%\from_%%D_Setup"
  call :copy_tree "%%D:\Windows\Logs\SetupDiag" "%RUN_DIR%\from_%%D_SetupDiag"
  call :copy_tree "%%D:\Windows\Minidump" "%RUN_DIR%\from_%%D_Minidump"
  call :copy_one "%%D:\Windows\INF\setupapi.dev.log" "%RUN_DIR%\from_%%D_setupapi.dev.log"
  call :copy_one "%%D:\Windows\INF\setupapi.offline.log" "%RUN_DIR%\from_%%D_setupapi.offline.log"
  call :copy_one "%%D:\SetupDiagResults.log" "%RUN_DIR%\from_%%D_SetupDiagResults.log"
  call :copy_one "%%D:\SetupDiagResults.xml" "%RUN_DIR%\from_%%D_SetupDiagResults.xml"
  call :copy_one "%%D:\Windows\Panther\Setup.etl" "%RUN_DIR%\from_%%D_Setup.etl"
)

echo [setuphelfer] Log collection finished. Review %RUN_DIR%
exit /b 0

:copy_tree
if exist "%~1\" (
  mkdir "%~2" 2>nul
  xcopy /E /I /Y /Q "%~1\*" "%~2\" >nul 2>&1
  echo copied_dir %~1>> "%RUN_DIR%\copy_index.txt"
)
exit /b 0

:copy_one
if exist "%~1" (
  copy /Y "%~1" "%~2" >nul 2>&1
  echo copied_file %~1>> "%RUN_DIR%\copy_index.txt"
)
exit /b 0
