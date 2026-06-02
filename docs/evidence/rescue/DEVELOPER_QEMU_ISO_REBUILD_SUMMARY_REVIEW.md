# Developer QEMU ISO Rebuild — Summary Review

**Datum:** 2026-06-03  
**Summary:** `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`  
**Log:** `build/rescue/logs/controlled-iso-build/latest.log`

## Summary

| Feld | Wert |
|------|------|
| Summary vorhanden | **yes** |
| run_id | `rescue_developer_iso_20260602_214335` |
| status | success |
| exit_code / LB_EXIT | **0** |
| rescue_build_profile | **developer-qemu** |
| iso_found | true |
| iso_path | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| iso_size | 511705088 |
| sha256 | `3ee02b364bf5a35106591b67fb975f0864390cb413088c0d000e54e770dd48c1` |
| started_at | 2026-06-02T23:43:35+02:00 |
| ended_at | 2026-06-02T23:47:16+02:00 |
| build_started | true |

## Log-Profil (Primärbeleg)

```
START 2026-06-02T23:43:35+02:00 profile=developer-qemu run_id=rescue_developer_iso_20260602_214335
POLICY_GUARD_STATUS=ready
LB_EXIT=0
```

## Bewertung

| Feld | Wert |
|------|------|
| Buildprofil laut Summary/Log | **developer-qemu** |
| Profil eindeutig verifiziert | **yes** |

## Status

**ok** (Profil korrekt; kein `profile=standard`)
