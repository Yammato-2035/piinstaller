@echo off
setlocal EnableExtensions
REM Disk / volume inventory only — no clean/format/convert/online destructive ops.

set "SCRIPT_DIR=%~dp0"
set "TAG_NAME=SETUP_LOGS.TAG"
set "OUT_ROOT="
set "RUN_DIR=%~1"

if not "%RUN_DIR%"=="" goto :have_outdir

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

:have_outdir
mkdir "%RUN_DIR%" 2>nul

echo list disk> "%RUN_DIR%\diskpart_script.txt"
echo list volume>> "%RUN_DIR%\diskpart_script.txt"
echo list partition>> "%RUN_DIR%\diskpart_script.txt"
diskpart /s "%RUN_DIR%\diskpart_script.txt" > "%RUN_DIR%\diskpart_output.txt" 2>&1

if exist "%SCRIPT_DIR%collect-win11-disk-info.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%collect-win11-disk-info.ps1" -OutDir "%RUN_DIR%"
)

wmic diskdrive get Model,SerialNumber,InterfaceType,Size,Status /format:list > "%RUN_DIR%\wmic_diskdrive.txt" 2>&1
wmic logicaldisk get DeviceID,VolumeName,FileSystem,Size,FreeSpace /format:list > "%RUN_DIR%\wmic_logicaldisk.txt" 2>&1
mountvol > "%RUN_DIR%\mountvol.txt" 2>&1

echo [setuphelfer] Disk info written to %RUN_DIR%
echo NOTE: No partitioning commands were executed.
exit /b 0
