# RESCUE_ISO_UEFI_AND_NETWORKMANAGER_FIX_RESULT

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_ISO_UEFI_AND_NETWORKMANAGER_FAILURE_TRIAGE_FIX`

## Version / HEAD

| | Wert |
|--|------|
| HEAD vorher | `ff2106d` |
| HEAD nachher | *(uncommitted workspace)* |
| Version vorher | `1.7.4.4` |
| Version nachher | **`1.7.4.5`** |
| Commit | ausstehend |
| Push | **nein** |

## Root Causes

| Bereich | Ursache |
|---------|---------|
| **UEFI** | live-build liefert nur ISOLINUX; Post-Patch nicht im Build-Wrapper |
| **NetworkManager** | `live-config-sysvinit` entfernt NM vor SquashFS; fehlendes `--initsystem systemd` |
| **Serial-Marker** | Stale Unit mit `TTYPath=/dev/ttyS0` im Build-Tree von früherem Profil; Prepare schrieb Unit nicht für Standard |

## Geänderte Dateien

- `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
- `scripts/rescue-live/validate-controlled-live-build-tree.sh`
- `scripts/rescue-live/run-controlled-iso-build-with-logging.sh`
- `backend/tests/test_rescue_developer_serial_visibility_v1.py`
- `config/version.json`, `VERSION`, `frontend/package.json`, … (sync-version)

## Tests

```text
python3 backend/tools/check_version_consistency.py  → OK (1.7.4.5)
bash -n prepare/validate/run-controlled-iso-build   → OK
unittest test_rescue_developer_serial_visibility_v1 → 18 OK
unittest test_version_consistency_v1                → OK
```

## Prepare / Validate

| Schritt | Ergebnis |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | **OK** — `--initsystem systemd`, NM-Hook, QEMU-only Serial-Unit |
| `validate-controlled-live-build-tree.sh` | **Exit 11** — `FORBIDDEN: …/binary/live/filesystem.squashfs` (Stale-Artefakt vom letzten Build; Operator-clean nötig) |

Konfigurations-Checks vor Forbidden-Scan: archive-areas, NM/wpasupplicant, Serial-Marker, initsystem — **grün**.

## ISO-Rebuild / Validator / SquashFS

| Check | Status |
|-------|--------|
| ISO-Rebuild | **nein** (sudo/Operator) |
| UEFI Validator | unverändert rot auf alter ISO |
| SquashFS nmcli/NM | unverändert auf alter ISO |
| SquashFS Firmware | iwlwifi-9000*, ibt-17-16-1, regdb weiterhin auf alter ISO |

## Gate / Evidence

- `iso_uefi_validated`: **false** (kein neuer Build)
- `usb_stick_written`: **false**
- `windows_inspect_executable`: **false**

## Blocker

**Resolved (Workspace):**

- Root Cause UEFI dokumentiert + Post-Patch im Build-Wrapper
- Root Cause NM dokumentiert + `--initsystem systemd` + NM-Hook
- Serial-Marker QEMU-only in Prepare

**Aktiv:**

- Stale `filesystem.squashfs` blockiert Validate Exit 0
- ISO-Rebuild + UEFI/NM-SquashFS-Verifikation ausstehend

## Next Prompt

**`RESCUE_ISO_UEFI_NETWORKMANAGER_REBUILD_OPERATOR_COMPLETION`**

```bash
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

## Nicht ausgeführt

USB-dd, MSI-Retest, Windows-Inspect, Deploy `/opt`, Push, Host-apt.
