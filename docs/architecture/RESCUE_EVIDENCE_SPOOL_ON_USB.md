# Rescue Evidence Spool on USB (FAT32 ESP)

## Zielpfade

```text
/setuphelfer/evidence/{boot,medium-check,network,telemetry,ui,hardware}/
/setuphelfer/logs/{boot,journal}/
/setuphelfer/profiles/machines/
/setuphelfer/state/rescue-state.json
```

## Regeln

- Keine Secrets in Logs/Evidence (`sanitize_rescue_log`)
- Keine WLAN-Passwörter
- Maschinenprofil ohne rohe Seriennummern
- JSON/JSONL/Text only
- Schreibfehler = `review_required`, kein Boot-Abbruch
- FAT32 read-only → Fallback `/run/setuphelfer/evidence`
- Spool-Sync best effort nach Medium-Check, vor UI

## Implementierung

`backend/rescue/rescue_evidence_spool.py`
