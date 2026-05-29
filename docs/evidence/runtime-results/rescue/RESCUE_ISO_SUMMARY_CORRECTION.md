# Rescue ISO Summary Correction

**Grund:** Wrapper suchte nur `*.iso`; live-build liefert `binary.hybrid.iso`.

| Feld | vorher | nachher |
|------|--------|---------|
| `iso_found` | false | **true** |
| `iso_path` | null | `…/binary.hybrid.iso` |
| `iso_size` | null | 507510784 |
| `sha256` | null | 03d5aa95… |
| `status` | failed | **review_required** |
| `error_code` | null | RESCUE-BUILD-ZSYNC-STALE-001 |
| `artifact_status` | — | partial_green |

`no_full_green`: true — kein Boot-Nachweis.

JSON: `rescue_iso_summary_correction_latest.json`, aktualisiert: `controlled_iso_build_latest_summary.json`
