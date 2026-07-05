# PI-RS-TEL-001 Knowledge Base (DE)

## Übersicht

| Aspekt | Wert |
|--------|------|
| Phase | PI-RS-TEL-001 |
| Vorarbeit | TEL-012 (Telemetry Server) |
| Client | `fake-rescue-stick-lab-client` |
| Modul | `backend/core/rescue_lab_telemetry_*.py` |
| API | `/api/rescue/telemetry/lab/*` |

## Module

1. `rescue_lab_telemetry_model.py` — Payload, PII-Validator, Envelope
2. `rescue_lab_telemetry_signing.py` — HMAC-v2, Nonce, Timestamp
3. `rescue_lab_telemetry_client.py` — HTTP POST zum Lab-Server
4. `rescue_lab_telemetry_status.py` — DCC-Status, letztes Ergebnis
5. `rescue_lab_telemetry_evidence.py` — redigierte Evidence-Exporte

## Operator-Checkliste

1. Lab-Profil setzen (`local_lab`, `developer` oder `rescue_lab`)
2. `SETUPHELPER_TELEMETRY_LAB_BASE_URL` konfigurieren
3. `SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET` setzen (nicht committen)
4. Einmalig `POST /api/rescue/telemetry/lab/send-preview` oder DCC-Button „Lab-Send testen“
5. Evidence unter `docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow/` prüfen

## Safety-Gate

`scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh`

## Roadmap

Nach PI-RS-TEL-001: **PI-RS-TEL-002** (Reachability + Offline-Queue-Preview).
