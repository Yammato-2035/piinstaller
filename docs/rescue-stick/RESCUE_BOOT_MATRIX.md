# Rescue Boot Matrix

**Stand:** 2026-06-17

| Systemklasse | Gerät | CPU | Firmware | Zielstatus | Evidence |
| ------------ | ----- | --- | -------- | ---------- | -------- |
| MSI Laptop | MSI (Dev) | x86_64 | UEFI | yellow | RS_F2B1, RS-P2 pending |
| ASUS ROG Laptop | — | x86_64 | UEFI | planned | — |
| Desktop AMD/Intel | Dev-Desktop | x86_64 | UEFI | planned | — |
| VM/QEMU Smoke | QEMU | x86_64 | UEFI | yellow | `docs/evidence/rescue/qemu_*` |
| Legacy BIOS | — | x86_64 | BIOS | planned | Testgerät fehlt |
| Dual-Boot | MSI | x86_64 | UEFI | yellow | nvme0 Win + nvme1 Linux |
| Raspberry Pi 5 | — | ARM64 | UEFI | planned | später |
| Raspberry Pi 4 | — | ARM64 | — | planned | später |

## Pflicht-Evidence pro Boot

`boot_id`, `stick_build_id`, `setuphelfer_version`, `boot_mode`, `kernel`, `network_status`, `detected_disks_redacted`, `detected_os`, `source_candidates`, `target_candidates`, `setup_logs_status`, `ui_started`, `backend_started`, `errors`, `warnings`
