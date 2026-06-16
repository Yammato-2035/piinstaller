# Modul-Contracts — Öffentliche Verträge pro Domäne

**Stand:** 2026-06-16  
**Prinzip:** Contracts sind **public-safe** — keine Server-Interna, keine Secrets, keine echten Produktions-Domains.

Jeder Contract trägt `CONTRACT_VERSION` (oder äquivalent) und wird durch Unit-Tests abgesichert.

---

## Übersicht nach Domäne

### `setuphelfer.platform`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Version API | `backend/api/routes/version.py` | `GET /api/version` — `project_version`, Runtime-Pfad |
| Health API | `backend/api/routes/health.py` | Liveness/Readiness ohne Secrets |

---

### `setuphelfer.core`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Storage Facade | `backend/core/storage_facade.py` | `get_block_devices`, `classify_storage_target`; `FACADE_CONTRACT_VERSION` |
| Mount Facade | `backend/core/mount_facade.py` | `build_readonly_mount_plan`, Mount-Safety (plan-only) |
| Safety Facade | `backend/core/safety_facade.py` | `validate_backup_target`, `SafetyContext`, Write-Target-Validierung |
| Partition Storage Facade | `backend/core/partition_storage_facade.py` | Partition-Ziele via Safety-Delegation |
| Redaction Contract | `backend/core/redaction_contract.py` | Kategorien, Test-Vektoren, lokale Preview |
| System Status Facade | `backend/core/system_status_facade.py` | Ampel-/Status-Aggregation (read-only) |
| Network Info Facade | `backend/core/network_info_facade.py` | Sichere Netzwerk-Metadaten |
| Webserver Status Facade | `backend/core/webserver_status_facade.py` | Webserver-Erreichbarkeit (read-only) |
| System Info Facade | `backend/core/system_info_facade.py` | Hardware-/OS-Klassifikation (redacted) |
| DCC Status Facade | `backend/core/dcc_status_facade.py` | DCC-Sections, Delegation read-only |

**Tests (Auszug):** `backend/tests/test_storage_facade_contracts_v1.py`, `test_mount_facade_contracts_v1.py`, `test_safety_facade_contracts_v1.py`, `test_redaction_contract_v1.py`

---

### `setuphelfer.backup_restore`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Audit Event Contract | `backend/core/audit_event_contract.py` | Struktur für Backup/Restore/Verify-Audit-Events |
| Runner Result Contract | `backend/deploy/runner_result_contract.py` | Einheitliche Runner-Ausgabe |
| Backup Readonly API | `backend/api/routes/backup_readonly.py` | Sichere GET-Endpunkte ohne Execute |

---

### `setuphelfer.inspect` / `setuphelfer.diagnostics_client`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Diagnostic Finding Contract | `backend/core/diagnostic_finding_contract.py` | `FindingSeverity`, `RecommendationMode.PLAN_ONLY`, `execute_allowed: false` |
| Dev Diagnostic Export | `docs/architecture/DEV_DIAGNOSTIC_EXPORT_CONTRACT.md` | Redacted Export für Fleet/QEMU |
| OpenAPI (plan-only) | `docs/api/diagnostics_client_contract_openapi.yaml` | Neutraler Client-Stub |

**Tests:** `backend/tests/test_diagnostic_finding_contract` (via Facade/Integration), Inspect-Contract-Tests

---

### `setuphelfer.telemetry_client`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Telemetry Client Contract | `backend/core/telemetry_client_contract.py` | `TelemetryClientEnvelope`, Opt-in, Redaction-Pflicht |
| Redaction Contract | `backend/core/redaction_contract.py` | Vorbedingung für jeden Send-Versuch |
| OpenAPI (public-safe) | `docs/api/telemetry_client_contract_openapi.yaml` | Beispiel-Domain `telemetry.internal.setuphelfer.example` |

**Tests:** `backend/tests/test_telemetry_client_contract_v1.py`

---

### `setuphelfer.rescue`

| Contract | Datei / Doku | Beschreibung |
|----------|--------------|--------------|
| Rescue Agent API | `docs/architecture/RESCUE_REMOTE_AGENT_CONTRACT.md` | Pairing, Ingest-Stubs |
| Rescue Fleet Session | `docs/architecture/DEV_CONTROL_CENTER_FLEET_SESSION_CONTRACT.md` | Lab-Sessions, Heartbeat |
| Rescue UI Launcher | `backend/rescue/rescue_ui_launcher_contract.py` | Stick-UI-Start (plan-only Gates) |
| Notification Events (Rescue) | `docs/architecture/NOTIFICATION_EVENT_CONTRACT.md` | `rescue_iso_*`, `rescue_usb_*` Event-Typen |

---

### `setuphelfer.deploy`

| Contract | Datei | Beschreibung |
|----------|-------|--------------|
| Runner API Facade | `backend/deploy/runner_api_facade.py` | Katalog, Plan-only Responses |
| Runner Result Contract | `backend/deploy/runner_result_contract.py` | Status, Evidence-Refs |
| Deploy Write Runner | `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_DE.md` | Write-Gate, Risk-Profile |

---

### `setuphelfer.dev_dashboard`

| Contract | Datei / Doku | Beschreibung |
|----------|--------------|--------------|
| Notification Event Contract | `docs/architecture/NOTIFICATION_EVENT_CONTRACT.md` | Persistente Events, E-Mail-Semantik |
| DCC Readonly Router | `backend/api/routes/dev_dashboard_readonly.py` | GET-only Aggregation |

**Tests:** `backend/tests/test_notification_event_contract_v1.py`

---

### Private Domänen (nur Referenz — Implementierung nicht im Public-Repo)

| Domäne | Public-Repo enthält | Private-Repo enthält |
|--------|---------------------|----------------------|
| `setuphelfer.cloudserver_edition` | Interface-Stubs, `docs/api/cloud_public_contracts_openapi.yaml` | Snapshot-Provider, inkrementelle Jobs |
| `setuphelfer.telemetry_server` | Client-Contract + OpenAPI-Stub | Ingest, Store, Signing |
| `setuphelfer.diagnostics_server` | `diagnostic_finding_contract` | Matcher, Session-Plane, KB-Ingest |
| `setuphelfer.operator_private` | Handoff-Docs unter `docs/private-handoff/` | Dashboard-UI, Lizenz/Billing |

---

## Contract-Disziplin

1. **Keine Secrets** in serialisierten Contract-Feldern (`message`, `title`, `payload`).  
2. **Redaction vor Send** bei Telemetrie (`redaction_applied: true` erforderlich).  
3. **Plan-only** bei Diagnostik (`recommendation_mode: plan_only`, `execute_allowed: false`).  
4. **Beispiel-Domains** in Doku/OpenAPI: `*.setuphelfer.example` — niemals echte interne Hosts.  
5. **Versionierung:** Breaking Changes → `CONTRACT_VERSION` erhöhen + Migration dokumentieren.

---

## Verwandte Dokumente

- [`CORE_FACADE_RULES.md`](CORE_FACADE_RULES.md)  
- [`CLOUD_TELEMETRY_PUBLIC_CONTRACTS.md`](CLOUD_TELEMETRY_PUBLIC_CONTRACTS.md)  
- [`docs/evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md`](../evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md)
