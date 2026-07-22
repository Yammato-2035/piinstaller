Setuphelfer WinPE / Windows Setup diagnostic helper
===================================================

Purpose:
  Capture Windows 11 setup logs and disk/boot inventory after an aborted
  install — without partitioning and without modifying install media.

Steps:
  1. Make SETUPHELFER_WIN_DIAG reachable from WinPE / Setup (FAT32).
  2. Run collect-win11-setup-logs.cmd as Administrator
     (invokes .ps1 helpers when available).
  3. Optional:
       - collect-win11-disk-info.cmd
       - collect-win11-boot-info.cmd OUTDIR
  4. Destination volume is found via SETUP_LOGS.TAG or label SETUP_LOGS
     (drive letters vary).
  5. Review the timestamped run folder, then reboot to the rescue stick
     to import logs.

Captures (when present):
  - Panther / Rollback / SetupDiag / DISM / CBS / setupapi
  - Get-Disk / Get-PhysicalDisk / UniqueId / serial (if available)
  - read-only diskpart list, bcdedit /enum, mountvol, EFI probe

Notes:
  - No passwords or BitLocker keys are collected.
  - No diskpart write commands (clean/format/convert/online).
  - No registry changes.
  - Raw identifiers stay on SETUP_LOGS only; git import must be redacted.
  - After another abort: collect logs first — no blind third retry.

Setuphelfer does not flash BIOS/firmware.
