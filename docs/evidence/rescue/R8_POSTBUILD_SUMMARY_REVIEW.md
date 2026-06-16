# R.8 — Post-Build Summary Review

**Datum:** 2026-06-13  
**Quellen:** `controlled_iso_build_latest_summary.json`, `build/rescue/logs/controlled-iso-build/latest.log`

## Summary JSON

| Check | Erwartung | Ergebnis |
|-------|-----------|----------|
| `exit_code` / LB_EXIT | 0 | **0** ✓ |
| `status` | success | **success** ✓ |
| `build_started` | true | **true** ✓ |
| `rescue_build_profile` | standard | **standard** ✓ |
| `run_id` | r8_clean_* | **r8_clean_20260613_201824** ✓ |
| `error_code` | null | **null** ✓ |
| `permission_denied_dot_build` | nein | **nein** ✓ |
| `policy_guard_status` | ready | **ready** (already_root) ✓ |

## UEFI

| Check | Ergebnis |
|-------|----------|
| Pre-build ISO ohne EFI | RESCUE-UEFI-001/002/003 (erwartet bei lb hybrid) |
| `UEFI_POST_PATCH: patch_rc=0` | **ja** |
| `validate_exit=0` | **ja** |
| Final: `BOOTX64=true EFI_IMG=true` | **ja** |

## Package / Build-Fehler

| Check | Ergebnis |
|-------|----------|
| `x-www-browser` Fehler im Log | **nicht gefunden** |
| apt/lb fatal error | **nicht** (LB_EXIT=0) |
| `permission_denied_dot_build` | **nicht** (Clean vor Build erfolgreich) |

## ISO-Output

```
ISO_SHA256=18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390
LB_EXIT=0
```

## Bewertung

**PASS** — Build erfolgreich, UEFI gepatcht und validiert.
