# Developer-QEMU ISO After Autopilot — Build Summary Review

**Datum:** 2026-06-03  
**Quelle:** `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`  
**Log:** `build/rescue/logs/controlled-iso-build/latest.log`

## Extrahierte Felder

| Feld | Wert |
|------|------|
| run_id | `rescue_developer_iso_20260602_220129` |
| started_at | `2026-06-03T00:01:29+02:00` |
| ended_at | `2026-06-03T00:05:09+02:00` |
| exit_code | `0` |
| LB_EXIT | `0` (Log-Tail) |
| rescue_build_profile | `developer-qemu` |
| iso_path | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| iso_found | `true` |
| sha256 | `614cc86ea865608f68524ef6d905a3baa1c0b1ce3dacaa9f1b80de6f541e0784` |
| iso_size | `511705088` |

## Log-Belege

```
START 2026-06-03T00:01:29+02:00 profile=developer-qemu run_id=rescue_developer_iso_20260602_220129
POLICY_GUARD_STATUS=ready
LB_EXIT=0
```

## Pflichtbewertung

| Kriterium | Ergebnis |
|-----------|----------|
| Summary vorhanden | yes |
| run_id | `rescue_developer_iso_20260602_220129` |
| log_path | `build/rescue/logs/controlled-iso-build/latest.log` |
| Buildprofil aus Summary | `developer-qemu` |
| Buildprofil aus Log | `developer-qemu` |
| LB_EXIT | `0` |
| profile verified | **yes** |
| Build erfolgreich | **yes** |

**Status:** `ok`
