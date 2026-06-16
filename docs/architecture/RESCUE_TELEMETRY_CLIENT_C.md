# Rescue Telemetry Client (Set C)

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.5.0

## Ziel

Öffentlichen `telemetry_client_contract` im Rettungsstick-Pfad anbinden — Opt-in, Redaction-before-send, keine Server-URL.

## Modul

`backend/core/rescue_telemetry_client.py`

| Funktion | Zweck |
|----------|-------|
| `build_rescue_stick_client_envelope` | Rescue-Report → `TelemetryClientEnvelope` |
| `build_rescue_stick_telemetry_client_preview` | UI/API-Vorschau inkl. `validation_errors` |
| `map_operator_consent_to_opt_in` | Consent-Mapping |
| `infer_data_categories` | Kategorie-Ableitung aus Rescue-Envelope |

## Integration

- `windows_rescue_inspect.ingest_operator_hardware_run` liefert `telemetry_client_preview` (opt-in default: disabled)
- Delegiert an `windows_rescue_inspect.build_telemetry_envelope` + `redaction_contract`

## Bewusst nicht gebaut

- Telemetrie-Server-Ingest (privat)
- Automatischer Send ohne Opt-in

## Tests

- `backend/tests/test_rescue_telemetry_client_v1.py`
- Regression: `test_telemetry_client_contract_v1.py`, `test_windows_rescue_inspect_v1.py`
