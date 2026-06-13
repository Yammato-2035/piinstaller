# R.4 — Telemetrie-Spool Integration

## Ziel

Upload-Fehler landen im R.3-Evidence-Spool unter `/setuphelfer-evidence/telemetry/spool/`.

## Änderungen

| Komponente | Änderung |
|------------|----------|
| `setuphelfer-rescue-common.sh` | `setuphelfer_rescue_r3_telemetry_spool`, `setuphelfer_rescue_r3_telemetry_mark_sent` |
| `setuphelfer-rescue-telemetry-push` | Ruft R.3-Spool bei network/health/ingest-Fehler; markiert sent bei HTTP 200 |
| `setuphelfer-rescue-evidence.py` | Subcommands `telemetry-spool`, `telemetry-mark-sent` |

## Event-ID

`<boot_id>-telemetry` — ein Event pro Boot-Versuch.

## Redaction

Über `rescue_telemetry_spool.py` — keine PSK/Token/Passwörter.

## Legacy-Spool

`/run/setuphelfer-rescue/telemetry-spool/` bleibt parallel für Retry-Timer-Kompatibilität.

## Matrix

`R4-TELEM-SPOOL-INT-001` = green wenn `setuphelfer_rescue_r3_telemetry_spool` im Push-Skript referenziert.

## Tests

`test_rescue_test_matrix_r4.py::test_telemetry_spool_integration_detected` — OK
