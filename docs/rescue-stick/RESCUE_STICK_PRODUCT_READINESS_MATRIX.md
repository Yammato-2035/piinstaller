# Rettungsstick Produkt-Readiness-Matrix (RS-P1)

**Stand:** 2026-06-17 · Version `1.9.5.0`

| Bereich | Fähigkeit | Status | Evidence | Blocker | Nächster Schritt |
| ------- | --------- | ------ | -------- | ------- | ---------------- |
| Boot | UEFI x86_64 | yellow | RS_F2B1, QEMU-Smoke | MSI-Retest offen | RS-P2 MSI-Boot |
| Boot | Legacy BIOS | planned | — | kein Testgerät | Bootmatrix erweitern |
| Boot | ARM64 / RPi | planned | — | später | nach x86-Abnahme |
| Boot | Secure Boot | yellow | dokumentiert | nicht signiert | Status dokumentieren |
| Boot | Schwarzer Bildschirm/Fallback | yellow | Boot-Menü-Assets | HW-Retest | RS-P2 |
| Systemerkennung | Windows/NTFS | green | `rescue_os_detection.py`, Tests | — | MSI-Runtime |
| Systemerkennung | Linux/ext4/btrfs/xfs | green | Core + Tests | — | MSI-Runtime |
| Systemerkennung | EFI/BIOS | yellow | `detect_boot_mode()` | Live-Evidence | RS-P2 |
| Systemerkennung | interne Platten | green | `rescue_disk_role_classifier` | — | — |
| Systemerkennung | externe Backupmedien | green | target policy | — | — |
| Systemerkennung | Rettungsstick selbst | green | blockiert als Ziel | — | — |
| Systemerkennung | SETUP_LOGS | green | blockiert als Ziel | — | — |
| Systemerkennung | Cloud nur plan-only | pro_only | Contract | kein Upload | private Repo |
| Telemetrie | SETUP_LOGS bevorzugt | yellow | F2B.1-Fix | MSI-Retest | RS-P2 |
| Telemetrie | Redaction | green | Tests grün | — | — |
| Telemetrie | no network upload | green | Contract | — | — |
| WLAN | LAN | green | nmcli | — | — |
| WLAN | unmanaged Fix | green | `setuphelfer_rescue_wifi_ensure_managed` | MSI-Retest | RS-P2 |
| WLAN | HDD ohne WLAN | green | `blocks_local_hdd_backup=false` | — | — |
| WLAN | Cloud ohne WLAN | blocked | Contract | — | — |
| Backup-Plan | manuelle Quell-/Zielwahl | green | Full-Plan API + UI | execute blocked | RS-P2 |
| Backup-Plan | externe HDD | green | policy + tests | — | — |
| Backup-Plan | Cloud Pro plan-only | pro_only | Contract | — | — |
| Full Backup | raw image Windows | yellow | Plan ready | execute blocked | RS-P3 |
| Full Backup | Linux full root tar | yellow | Plan ready | execute blocked | RS-P3 |
| Verify | Contract | contract_ready | `rescue_backup_verify_contract.py` | kein Execute | RS-P3 |
| Encryption | Contract | review_required | `rescue_backup_encryption_contract.py` | Key deferred | RS-P3 |
| Restore | Preview/Dry | planned | Doku | blockiert | RS-P4+ |
