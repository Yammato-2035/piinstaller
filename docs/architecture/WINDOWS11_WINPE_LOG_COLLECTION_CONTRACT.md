# WINDOWS11_WINPE_LOG_COLLECTION_CONTRACT

**Path:** `scripts/rescue-live/image/SETUPHELFER_WIN_DIAG/`

## Required files

- `README_DE.txt`, `README_EN.txt`
- `collect-win11-setup-logs.cmd` / `.ps1`
- `collect-win11-disk-info.cmd` / `.ps1`
- `collect-win11-boot-info.cmd`
- `SETUP_LOGS.TAG`

## Behaviour

1. Locate destination via `SETUP_LOGS.TAG` or volume label `SETUP_LOGS` (letters vary).
2. Create run folder with timestamp + run id.
3. Inventory disks/volumes (Get-Disk / diskpart list / wmic / mountvol).
4. Copy Panther, Rollback, SetupDiag, DISM, CBS, setupapi, Minidump when present.
5. Capture BCD/EFI probe read-only.
6. Never partition, never Online-Disk, never edit registry, never capture credentials.
7. Raw identifiers stay on SETUP_LOGS; git import must be redacted.
