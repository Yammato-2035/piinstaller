@echo off
setlocal EnableExtensions
REM Disk / BCD inventory only — no clean/format/convert/select destructive ops.

set "SCRIPT_DIR=%~dp0"
set "TAG_NAME=SETUP_LOGS.TAG"
set "OUT_ROOT="
set "STAMP="

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%I"
if "%STAMP%"=="" set "STAMP=unknown"

for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\%TAG_NAME%" set "OUT_ROOT=%%D:\setuphelfer-win11-logs"
)
if "%OUT_ROOT%"=="" (
  for /f "skip=1 tokens=1,2*" %%A in ('wmic volume get DriveLetter^,Label 2^>nul') do (
    if /I "%%B"=="SETUP_LOGS" if not "%%A"=="" set "OUT_ROOT=%%A\setuphelfer-win11-logs"
  )
)
if "%OUT_ROOT%"=="" (
  echo [setuphelfer] ERROR: SETUP_LOGS destination not found.
  exit /b 2
)

set "RUN_DIR=%OUT_ROOT%\%STAMP%-diskinfo"
mkdir "%RUN_DIR%" 2>nul

echo list disk> "%RUN_DIR%\diskpart_list_disk.txt"
echo list volume>> "%RUN_DIR%\diskpart_list_disk.txt"
diskpart /s "%RUN_DIR%\diskpart_list_disk.txt" > "%RUN_DIR%\diskpart_output.txt" 2>&1

bcdedit /enum all > "%RUN_DIR%\bcdedit_enum_all.txt" 2>&1
pnputil /enum-devices /connected > "%RUN_DIR%\pnputil_devices.txt" 2>&1

echo [setuphelfer] Disk info written to %RUN_DIR%
echo NOTE: No partitioning commands were executed.
exit /b 0
