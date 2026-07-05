# PI-RS-TEL-001 Knowledge Base (EN)

## Overview

| Aspect | Value |
|--------|------|
| Phase | PI-RS-TEL-001 |
| Prerequisite | TEL-012 (telemetry server) |
| Client | `fake-rescue-stick-lab-client` |
| Modules | `backend/core/rescue_lab_telemetry_*.py` |
| API | `/api/rescue/telemetry/lab/*` |

## Modules

1. `rescue_lab_telemetry_model.py` — payload, PII validator, envelope
2. `rescue_lab_telemetry_signing.py` — HMAC-v2, nonce, timestamp
3. `rescue_lab_telemetry_client.py` — HTTP POST to lab server
4. `rescue_lab_telemetry_status.py` — DCC status, last result
5. `rescue_lab_telemetry_evidence.py` — redacted evidence exports

## Operator checklist

1. Set lab profile (`local_lab`, `developer`, or `rescue_lab`)
2. Configure `SETUPHELPER_TELEMETRY_LAB_BASE_URL`
3. Set `SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET` (do not commit)
4. One-shot `POST /api/rescue/telemetry/lab/send-preview` or DCC “Lab-Send testen” button
5. Review evidence under `docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow/`

## Safety gate

`scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh`

## Roadmap

After PI-RS-TEL-001: **PI-RS-TEL-002** (reachability + offline queue preview).
