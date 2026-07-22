# Windows 11 Install Diagnostic Contract

**Module:** `rescue_windows11_install_diag.py`  
**WinPE helper:** `scripts/rescue-live/image/SETUPHELFER_WIN_DIAG/`

## Sequence

1. Evidence scan (Panther/Rollback) read-only  
2. Media check (structure + optional SHA256)  
3. Preflight (`write_allowed=false`)  
4. Abort cause matrix  
5. Destructive plan only after dual confirmation  
6. Postcheck before Linux gate

## Error classes

storage_driver, nvme_controller, intel_vmd_or_rst, partition_layout, gpt_or_uefi_mismatch,
secure_boot_or_tpm, unsupported_hardware, memory_error, media_corruption, image_error,
driver_installation, update_phase, first_boot_phase, bootloader, unexpected_reboot,
power_or_thermal, unknown
