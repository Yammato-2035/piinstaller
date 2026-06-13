# R.3 — Telemetrie-Spool Evidence

**Modul:** `backend/core/rescue_telemetry_spool.py`  
**Pfad:** `setuphelfer-evidence/telemetry/spool/`  
**Tests:** `backend/tests/test_rescue_telemetry_spool_r3.py` (2 Tests, OK)

## API

| Funktion | Zweck |
|----------|-------|
| `write_telemetry_event()` | JSON-Event in Spool (redacted) |
| `list_pending_telemetry_events()` | Noch nicht gesendete Events |
| `mark_telemetry_event_sent()` | Nach erfolgreichem Upload markieren |
| `build_telemetry_spool_summary()` | Zähler + letzte Fehler |

## Redaction

- `password`, `psk`, `token`, `secret` → `[REDACTED]`
- WLAN-PSK wird **nie** gespeichert

## Format

Einzelne JSON-Dateien pro Event (`<event_id>.json`) mit `sent: false|true`.

## Offen

`setuphelfer-rescue-telemetry-push` — Spool-Integration in R.4 (Upload-Fehler → pending bleibt sichtbar).
