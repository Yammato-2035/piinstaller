@echo off
setlocal EnableExtensions
REM Boot / EFI / BCD inventory — read-only.

set "RUN_DIR=%~1"
if "%RUN_DIR%"=="" (
  echo Usage: collect-win11-boot-info.cmd OUTDIR
  exit /b 2
)
mkdir "%RUN_DIR%" 2>nul

bcdedit /enum all > "%RUN_DIR%\bcdedit_enum_all.txt" 2>&1
bcdedit /enum firmware > "%RUN_DIR%\bcdedit_enum_firmware.txt" 2>&1
mountvol > "%RUN_DIR%\mountvol_boot.txt" 2>&1

REM EFI system volumes via mountvol (letters vary)
echo. > "%RUN_DIR%\efi_volume_probe.txt"
for %%D in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if exist "%%D:\EFI\Microsoft\Boot\bootmgfw.efi" echo %%D: EFI Microsoft Boot>> "%RUN_DIR%\efi_volume_probe.txt"
  if exist "%%D:\EFI\Boot\bootx64.efi" echo %%D: EFI Boot bootx64>> "%RUN_DIR%\efi_volume_probe.txt"
)

pnputil /enum-drivers > "%RUN_DIR%\pnputil_enum_drivers.txt" 2>&1
pnputil /enum-devices /connected > "%RUN_DIR%\pnputil_devices.txt" 2>&1

echo [setuphelfer] Boot info written to %RUN_DIR%
echo NOTE: No BCD writes were performed.
exit /b 0
