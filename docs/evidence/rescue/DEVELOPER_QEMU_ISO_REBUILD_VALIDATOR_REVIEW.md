# Developer QEMU ISO Rebuild — Validator Review

**Datum:** 2026-06-03  
**Log:** `developer_qemu_iso_rebuild_squashfs_validator_latest.log`

## Squashfs-Validator

| Feld | Wert |
|------|------|
| Skript | `validate-rescue-iso-squashfs.sh` |
| Exit | **0** |
| Meldung | OK: bundle, systemd init, enabled units, de keyboard/locale, login hints |

**Limitation:** Validator prüft nur `setuphelfer-backend` + `setuphelfer.service` in wants — **nicht** `setuphelfer-qemu-smoke-autopilot.service`.

## Log-Warnungen

| Typ | Fatal? |
|-----|--------|
| `cp: … binary/isolinux/*.fnt` … (6× wildcard) | **no** — bekannte live-build-Wildcard-Warnung |
| `update-rc.d: warning` | **no** |
| `profile=developer-qemu` im Log | **yes** (Zeile 1) |

## Status

**review_required** — Validator grün für Standard-Checks; Autopilot-Enable-Gap nicht abgedeckt.
