Setuphelfer WinPE / Windows Setup diagnostic helper
===================================================

Purpose:
  Collect Windows 11 setup logs and disk inventory after an aborted
  install — without partitioning and without modifying install files.

Steps:
  1. Make SETUPHELFER_WIN_DIAG available in WinPE / Windows Setup (FAT32).
  2. Run collect-win11-setup-logs.cmd as Administrator.
  3. Optionally run collect-win11-disk-info.cmd.
  4. Destination volume is found via SETUP_LOGS label or SETUP_LOGS.TAG.
  5. Review the timestamped output folder, then boot the rescue stick
     to import and analyze the logs.

Notes:
  - No passwords or BitLocker keys are collected.
  - No destructive diskpart commands (clean/format/convert).
  - Drive letters vary — do not assume C:.
  - After another abort: collect logs, analyze on the rescue stick —
    do not blindly retry a third time.

Setuphelfer does not flash BIOS/firmware automatically.
