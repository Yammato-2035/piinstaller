# G513QM Windows 11 Retest — BIOS 331 Runbook

**Task:** PI-RS-ASUS-WIN11-RETEST-005 Stage A

## Preconditions

- Machine bound: `asus_rog_gabriel` / G513QM
- BIOS installed: **G513QM.331** (do not flash)
- Windows + Linux NVMe role binding operator-confirmed
- Linux NVMe isolated (physical preferred)
- Official Windows 11 x64 media checked
- WinPE collector on FAT32 (`SETUPHELFER_WIN_DIAG`)
- SETUP_LOGS writable

## Phrases (exact)

1. `WINDOWS-ZIEL G513QM BESTÄTIGT`
2. `WINDOWS-NVME VOLLSTÄNDIG LÖSCHEN`

## Install

1. Boot official Windows media (UEFI).
2. In WinPE before Install: inventory disks; confirm Linux NVMe offline/absent; confirm Windows identity.
3. Delete partitions **only** on Windows NVMe; let Setup create GPT/EFI/MSR/Recovery.
4. Record phase, progress, reboots, last text, error code, abort time.
5. On abort: Shift+F10 → run collector → shut down. Do **not** start another install loop.

## After run

Import SETUP_LOGS → redaction gate → SetupDiag offline → `windows_setup_331_result.json`.
