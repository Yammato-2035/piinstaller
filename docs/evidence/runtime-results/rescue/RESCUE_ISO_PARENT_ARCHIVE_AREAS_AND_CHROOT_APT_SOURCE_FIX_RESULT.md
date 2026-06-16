# RESCUE_ISO_PARENT_ARCHIVE_AREAS_AND_CHROOT_APT_SOURCE_FIX_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_ISO_PARENT_ARCHIVE_AREAS_AND_CHROOT_APT_SOURCE_FIX`  
**HEAD:** `2a36003` → Commit Phase 11 · **Version:** **`1.7.4.4`**

## Ergebnis

**Workspace-Fix grün, ISO-Rebuild ausstehend (Operator sudo + chroot clean).** Parent-Mirror-APT-Quellen und quoted `archive-areas` korrigiert; Build-Tree-Validator Exit 0.

## Root Cause

| Problem | Wirkung |
|---------|---------|
| Unquoted `--archive-areas main contrib …` | `lb config` erhielt nur **`main`** |
| Fehlende `debian.list.chroot` | Chroot `sources.list` blieb `bookworm main` |
| Nur Security-Listen mit `non-free-firmware` | Security ok, Parent weiterhin ohne Firmware |

## Fix

| Datei | Änderung |
|-------|----------|
| `prepare-controlled-live-build-tree.sh` | `--archive-areas 'main contrib non-free-firmware'` |
| `config/archives/debian.list.chroot` | Parent: `deb … bookworm main contrib non-free-firmware` |
| `config/archives/debian.list.binary` | gleich |
| `validate-controlled-live-build-tree.sh` | `RESCUE-ISO-PARENT-APT-SOURCE-001` |

## Tests

23/23 unittest OK · Prepare OK · Validate **Exit 0**

## Operator (Rebuild)

```bash
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

**Wichtig:** Stale `chroot/etc/apt/sources.list` (main-only) wird erst nach **clean** ersetzt.

## Erfolgskriterien ISO

Noch **nicht grün** — Squashfs-/UEFI-Nachweis ausstehend.

## Next Prompt

`RESCUE_ISO_MSI_FIRMWARE_REBUILD_OPERATOR_SUDO_COMPLETION`
