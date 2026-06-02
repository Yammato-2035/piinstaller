# Rescue ISO Build-Tree Cleanup — Script Review

**Stand:** 2026-06-02  
**Status:** **ok**

## Skript

`scripts/rescue-live/clean-controlled-live-build-tree.sh`

| Kriterium | Bewertung |
|-----------|-----------|
| Nur Build-Tree | **yes** — `BUILD_ROOT=.../setuphelfer-rescue-live` |
| Operator-Confirm | **`--operator-confirm-clean`** erforderlich |
| Dry-Run | **`--dry-run`** vorhanden |
| Kein USB/dd/mkfs | **yes** — Forbidden in usage |
| Kein breites rm | **yes** — `list_clean_targets()` aus Permission-Policy |
| Keine Host-Disk | **yes** |

## Begleit-Skripte

| Skript | Syntax |
|--------|--------|
| `prepare-controlled-live-build-tree.sh` | **ok** |
| `validate-controlled-live-build-tree.sh` | **ok** |

## Clean-Targets (Dry-Run)

13 Pfade unter `BUILD_ROOT` only: `.build`, `binary`, `binary.hybrid.iso`, `chroot`, `cache`, `local`, …

Kein `/dev`, kein `/opt`, kein USB.
