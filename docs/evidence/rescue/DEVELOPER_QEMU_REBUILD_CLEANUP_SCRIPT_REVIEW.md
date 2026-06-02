# Developer QEMU Rebuild — Cleanup Script Review

**Datum:** 2026-06-02  
**Skript:** `scripts/rescue-live/clean-controlled-live-build-tree.sh`

## Safety

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Nur Build-Tree | **yes** (`BUILD_ROOT` unter Repo, `realpath`-Guard) |
| Operator-Confirm | **yes** (`--operator-confirm-clean`) |
| Dry-Run | **yes** (Default + `--dry-run`) |
| Kein USB/dd/mkfs/restore | **yes** (nur `rm -rf` auf Allowlist aus `list_clean_targets`) |
| findmnt/umount | **nein** im Skript |
| Forbidden paths | /opt, /dev, /media, /mnt, git, apt, dd, mount — dokumentiert |

`bash -n`: **ok**

## Status

**ok**
