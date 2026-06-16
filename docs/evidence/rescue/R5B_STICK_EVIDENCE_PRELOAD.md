# R.5B — Stick Evidence Preload

**Datum:** 2026-06-13

## Status

**Nicht vorbereitet** — Write nicht ausgeführt.

## Geplante Stick-Pfade (nach Write)

| Pfad auf Stick | Inhalt |
|----------------|--------|
| `/setuphelfer-evidence/summaries/r5b_usb_write_summary.md` | Human summary |
| `/setuphelfer-evidence/summaries/r5b_usb_write_summary.json` | Machine summary |

## JSON-Schema (Entwurf)

```json
{
  "schema_version": 1,
  "phase": "R5B",
  "iso_sha256": "f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143",
  "usb_target_redacted": "/dev/sdX",
  "write_time_utc": null,
  "verify_status": null,
  "msi_next_steps": [
    "UEFI boot SETUPHELFER",
    "Kiosk/React UI smoke",
    "WLAN menu read-only",
    "Evidence auf Stick prüfen"
  ],
  "forbidden": ["internal_disks", "backup", "restore", "partition_write"]
}
```

## Hinweis

Stick-Summaries erst nach erfolgreichem Write + Verify durch Operator oder Writer-Finalize erstellen. **Nicht committen** mit Seriennummern oder unredacted `/dev/*`.
