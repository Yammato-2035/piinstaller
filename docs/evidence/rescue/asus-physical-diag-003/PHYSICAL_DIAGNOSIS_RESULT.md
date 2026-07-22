# PHYSICAL_DIAGNOSIS_RESULT — PI-RS-ASUS-PHYSICAL-DIAG-003

## Status

`diagnosis_incomplete`

## Letzter Import

- Run: `import-gabriel-20260722-204422-early-blackscreen`
- Cmdline: `hardware_discovery` korrekt (MSI aus, auto_shutdown=0)
- Identity: G513QM ✓
- TUI/GUI: nein — Konsole auf **dummy device** nach amdgpu-Modeset
- Capture: nur early; kein NVMe/Panther

## Stick-Fix nach Import

GRUB Hardwarediagnose jetzt mit:
`setuphelfer_mode=text nomodeset modprobe.blacklist=nouveau nouveau.modeset=0`
