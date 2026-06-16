# Public/Private Boundary Rules

**Stand:** 2026-06-16  
**Gate-Skript:** `scripts/check-public-private-boundary.sh`  
**Ergänzung:** `scripts/check-private-import-boundaries.sh`

## Zweck

Verhindern, dass proprietäre Cloudserver-Edition, interner Telemetrie-Server, Diagnostikserver-Interna, Operator-Dashboard, Lizenz-/Billinglogik oder Secrets in ein öffentliches GitHub-Repository gelangen.

## Verbotene Pfade (öffentlicher Kontext)

| Pfad | Kategorie |
|------|-----------|
| `backend/cloudserver_private/` | Cloudserver privat |
| `backend/cloudserver_edition/` | Cloudserver privat |
| `backend/telemetry_server/` | Telemetrie intern |
| `backend/internal_telemetry/` | Telemetrie intern |
| `backend/diagnostics_server/` | Diagnostik intern |
| `backend/internal_diagnostics/` | Diagnostik intern |
| `backend/operator_dashboard/` | Operator privat |
| `frontend/src/pages/CloudOperatorDashboard.tsx` | Operator privat |
| `frontend/src/operator/` | Operator privat |
| `commercial/`, `licensing/`, `billing/`, `subscriptions/` | Kommerziell |
| `private/`, `internal/`, `secrets/` | Privat |
| `deploy/production/`, `infra/production/` | Produktion |

## Verbotene Begriffe (staged/geändert)

`CLOUDSERVER_PRO_LICENSE`, `CLOUDSERVER_COMMERCIAL`, `TELEMETRY_SERVER_SECRET`, `INTERNAL_TELEMETRY_INGEST`, `OPERATOR_DASHBOARD`, `INTERNAL_DIAGNOSTIC_RULE`, `HARDWARE_FINGERPRINT_PRIVATE`, `CUSTOMER_BILLING`, `LICENSE_ENFORCEMENT`, `PRIVATE_INGEST`, `PLESK_CATALOG_SUBMISSION_SECRET`, `IONOS_PRODUCTION_TOKEN`, `PLESK_API_TOKEN`, `SMTP_PASSWORD`, `JWT_SECRET`, `CLIENT_SIGNING_PRIVATE_KEY`, `TELEMETRY_SIGNING_PRIVATE_KEY`

## Erlaubte Platzhalter-Domains

- `telemetry.internal.setuphelfer.example`
- `operator.internal.setuphelfer.example`
- `diagnose.internal.setuphelfer.example`
- `cloud.private.setuphelfer.example`
- `api.internal.setuphelfer.example`

## Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | OK |
| 10 | private_code_detected |
| 11 | internal_telemetry_detected |
| 12 | commercial_logic_detected |
| 13 | secret_pattern_detected |
| 14 | operator_dashboard_detected |
| 15 | public_db_port_detected |
| 16 | private_domain_detected |
| 20 | review_required |
| 99 | unknown_error |

## Public-safe im öffentlichen Repo

- `backend/core/*_facade.py`, `*_contract.py` (ohne Server-Interna)
- `docs/architecture/*`, `docs/api/*` (Contracts)
- `docs/private-handoff/*` (Handoff, keine Implementierung)
- Boundary-Gate-Skripte und zugehörige Tests

## Private-only (nur separates privates Repo)

- Cloudserver Edition Implementierung
- Telemetrie-Server Ingest/Store/Operator-API
- Diagnostikserver interne Regeln
- Operator-Dashboard UI
- Lizenz-/Billing-/Abo-Logik
- Plesk-Free-Produkt (später)
