# Controlled ISO Build — Summary Ingest

**Datum:** 2026-06-02  
**Summary:** `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`

## Auswertung

| Feld | Wert |
|------|------|
| Summary vorhanden | **yes** |
| status | `success` |
| exit_code / LB_EXIT | **0** |
| iso_found | **true** |
| iso_path | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| iso_size | 511705088 |
| sha256 | `505989f7d348265c08e8baeaa2971f81aa855224223859ae8d536b984dafaf52` |
| started_at | 2026-06-02T21:55:02+02:00 |
| finished_at | 2026-06-02T21:58:46+02:00 |
| Dauer | ~224 s |
| log_path (Wrapper) | `build/rescue/logs/controlled-iso-build/latest.log` |
| rescue_build_profile | `standard` |
| usb_write_allowed | false |
| dd_executed | false |

## Bewertung

**Status: ok**

Build-Zeitpunkt plausibel (nach Cleanup/Validate-Fix am 2026-06-02). Summary und Log konsistent mit LB_EXIT=0.
