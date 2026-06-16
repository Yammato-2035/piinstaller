# Cloud & Telemetrie — Öffentliche Contracts

**Stand:** 2026-06-16  
**Scope:** Public-safe Schnittstellen für Cloudserver- und Telemetrie-**Clients** — keine Server-Implementierung.

---

## Dateien

| Artefakt | Pfad | Zweck |
|----------|------|-------|
| Telemetry Client OpenAPI | `docs/api/telemetry_client_contract_openapi.yaml` | Opt-in Report-Envelope |
| Diagnostics Client OpenAPI | `docs/api/diagnostics_client_contract_openapi.yaml` | Plan-only Findings |
| Cloud Public Stubs | `docs/api/cloud_public_contracts_openapi.yaml` | Neutrale Cloud-Edition-Stubs |

Python-Referenzimplementierung (Client-seitig):

- `backend/core/telemetry_client_contract.py`
- `backend/core/diagnostic_finding_contract.py`
- `backend/core/redaction_contract.py`

---

## Gemeinsame Regeln

1. **Beispiel-Domains only:** `*.setuphelfer.example`  
2. **Keine Execute-Operationen** in public Diagnostics/Cloud-Stubs  
3. **Redaction-before-send** für Telemetrie  
4. **CONTRACT_VERSION** / `schema_version` bei Breaking Changes erhöhen  
5. **Keine Authentifizierungs-Secrets** in OpenAPI-Beispielen (Platzhalter `Bearer <token-from-config>`)

---

## Telemetry Client — Pflichtfelder (logisch)

| Feld | Typ | Hinweis |
|------|-----|---------|
| `schema_version` | integer | Envelope-Version |
| `opt_in_state` | enum | Consent-Pflicht |
| `data_categories` | string[] | Explizite Kategorien |
| `redaction_applied` | boolean | Muss true sein |
| `local_preview_ok` | boolean | Vorschau bestätigt |
| `payload` | object | Bereits redigiert |
| `contract_version` | integer | Parallel zu Python-Modul |

---

## Diagnostics Client — Pflichtfelder (logisch)

| Feld | Typ | Hinweis |
|------|-----|---------|
| `code` | string | Stabiler Finding-Code |
| `severity` | enum | info … critical |
| `recommendation_mode` | enum | `plan_only` |
| `execute_allowed` | boolean | Immer `false` im Public-Contract |

---

## Cloud Stubs — Zweck

Neutrale Platzhalter für spätere private Endpunkte:

- `GET /v1/cloud/capabilities` — Feature-Flags (Stub)
- `POST /v1/cloud/backup/plan` — Plan-only, keine Ausführung

Implementierung: ausschließlich Private-Repo.

---

## Tests

- `backend/tests/test_telemetry_client_contract_v1.py`
- `backend/tests/test_redaction_contract_v1.py`
- Facade-/Contract-Tests für Findings (Inspect-Pipeline)

---

## Verwandte Dokumente

- [`TELEMETRY_INTERNAL_ONLY_CONCEPT.md`](TELEMETRY_INTERNAL_ONLY_CONCEPT.md)  
- [`CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md`](CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md)  
- [`MODULE_CONTRACTS.md`](MODULE_CONTRACTS.md)
