# RESCUE_ISO_PARENT_ARCHIVE_AREAS_FIX_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_ISO_PARENT_ARCHIVE_AREAS_AND_CHROOT_APT_SOURCE_FIX`

## Ergebnis

**Build LB_EXIT=0 (2026-06-06), Firmware im SquashFS grün.** UEFI-Validator Exit **34**, NetworkManager/nmcli im SquashFS **fehlend** — siehe `RESCUE_ISO_BUILD_SUCCESS_VALIDATION_RESULT.md`. USB-Rewrite **noch nicht** freigegeben.

## Git / Version

| | Vorher | Nachher |
|---|--------|---------|
| HEAD | `2a36003` | Commit Phase 12 |
| Version | `1.7.4.3` | **`1.7.4.4`** |
| Commit | — | ja |
| Push | — | nein |

## Fix

| Bereich | Änderung |
|---------|----------|
| `auto/config` | Quoted `--archive-areas` + `--parent-archive-areas` |
| `config/archives/debian.list.*` | Parent `bookworm` + `bookworm-updates` mit `non-free-firmware` |
| Validator | Parent/chroot/security completeness + Diagnosecodes |
| Tests | 23/23 OK |

## Prepare / Validate

| Schritt | Ergebnis |
|---------|----------|
| Prepare | **OK** |
| Validate (stale chroot) | **rot** `RESCUE-ISO-CHROOT-SOURCES-NONFREE-FIRMWARE-MISSING-001` (erwartet bis sudo clean) |
| Validate (nach Operator-clean) | erwartet **grün** |

## ISO-Rebuild

| Feld | Wert |
|------|------|
| Agent sudo clean | **blockiert** |
| Agent ISO build | **nicht ausgeführt** |
| Alte ISO SHA256 | `09b9482a4ef18e2abf091edace794fc6baa27398f44b26e131db87ca855e0879` |
| Neue SHA256 | **n/a** |
| LB_EXIT | **n/a** (Rebuild ausstehend) |

## Operator

```bash
cd /home/volker/piinstaller
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Build-Log muss zeigen: `bookworm/non-free-firmware amd64 Packages`

## Erfolgskriterien

**Nicht vollständig grün** — ISO/Squashfs/UEFI ausstehend.

## Next Prompt

`RESCUE_ISO_MSI_FIRMWARE_REBUILD_OPERATOR_SUDO_COMPLETION` → bei Erfolg `RESCUE_USB_REWRITE_OPERATOR_AFTER_MSI_FIRMWARE_REBUILD`

## Nicht ausgeführt

USB-dd, MSI-Retest, Windows-Inspect, Deploy, Push, Host-apt
