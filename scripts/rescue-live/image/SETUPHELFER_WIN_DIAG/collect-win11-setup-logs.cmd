@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM Setuphelfer WinPE collector — read-only copy of Windows Setup logs.
REM No partitioning. No credential capture. No install media modification.

set "SCRIPT_DIR=%~dp0"
set "TAG_NAME=SETUP_LOGS.TAG"
set "OUT_ROOT="
set "STAMP="

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%I"
if "%STAMP%"=="" set "STAMP=unknown"

echo [setuphelfer] Searching for SETUP_LOGS destination...
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\%TAG_NAME%" set "OUT_ROOT=%%D:\setuphelfer-win11-logs"
  if /I "%%~D"=="" rem noop
)
REM Also match volume label SETUP_LOGS via wmic if available
if "%OUT_ROOT%"=="" (
  for /f "skip=1 tokens=1,2*" %%A in ('wmic volume get DriveLetter^,Label 2^>nul') do (
    if /I "%%B"=="SETUP_LOGS" if not "%%A"=="" set "OUT_ROOT=%%A\setuphelfer-win11-logs"
  )
)

if "%OUT_ROOT%"=="" (
  echo [setuphelfer] ERROR: SETUP_LOGS.TAG / label SETUP_LOGS not found.
  echo Place the rescue SETUP_LOGS partition or copy SETUP_LOGS.TAG to the target volume.
  exit /b 2
)

set "RUN_DIR=%OUT_ROOT%\%STAMP%"
mkdir "%RUN_DIR%" 2>nul
echo [setuphelfer] Output: %RUN_DIR%

echo setuphelfer_win_diag=1> "%RUN_DIR%\collector_meta.txt"
echo stamp=%STAMP%>> "%RUN_DIR%\collector_meta.txt"
echo computername=%COMPUTERNAME%>> "%RUN_DIR%\collector_meta.txt"

REM Inventory all drive roots (letters vary)
echo. > "%RUN_DIR%\drive_roots.txt"
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\" echo %%D:>> "%RUN_DIR%\drive_roots.txt"
)

call :copy_tree "X:\Windows\Panther" "%RUN_DIR%\from_X_Windows_Panther"
call :copy_tree "X:\Windows\System32\LogFiles" "%RUN_DIR%\from_X_LogFiles"

for %%D in (C D E F G H I J K L M N O P Q R S T U V W Y Z) do (
  call :copy_tree "%%D:\$WINDOWS.~BT\Sources\Panther" "%RUN_DIR%\from_%%D_WINDOWS_BT_Panther"
  call :copy_tree "%%D:\$WINDOWS.~BT\Sources\Rollback" "%RUN_DIR%\from_%%D_WINDOWS_BT_Rollback"
  call :copy_tree "%%D:\Windows\Panther" "%RUN_DIR%\from_%%D_Windows_Panther"
  call :copy_one "%%D:\Windows\INF\setupapi.dev.log" "%RUN_DIR%\from_%%D_setupapi.dev.log"
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
