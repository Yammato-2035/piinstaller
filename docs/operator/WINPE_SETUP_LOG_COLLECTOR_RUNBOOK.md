# WinPE Setup Log Collector Runbook

See also: `docs/architecture/WINDOWS11_WINPE_LOG_COLLECTION_CONTRACT.md`

1. Ensure `SETUPHELFER_WIN_DIAG/` is on a FAT32 volume reachable from WinPE.
2. Ensure destination has `SETUP_LOGS.TAG` or label `SETUP_LOGS`.
3. Run `collect-win11-setup-logs.cmd` as Administrator.
4. Optional: `collect-win11-disk-info.cmd`, `collect-win11-boot-info.cmd OUTDIR`.
5. Copy run folder off the stick; redact before git.
6. Never run clean/format/online disk from these scripts.
