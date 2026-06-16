# Modulgrenzen — Domänenkatalog

**Stand:** 2026-06-16  
**Status:** Verbindlich für neue Entwicklung · Monolith-Entkopplung läuft (siehe [`MONOLITH_BOUNDARY_MAP.md`](MONOLITH_BOUNDARY_MAP.md))  
**Gate:** `scripts/check-module-boundaries.sh`, `scripts/check-public-private-boundary.sh`

Dieses Dokument definiert **15 Domänen** (`setuphelfer.*`) mit Import-Regeln. Öffentliche Domänen leben im Public-Repository; private Domänen nur im separaten Private-Repository (siehe [`PUBLIC_PRIVATE_MODULE_BOUNDARIES.md`](PUBLIC_PRIVATE_MODULE_BOUNDARIES.md)).

---

## Domänentabelle

| Domäne | Verantwortlich für | Darf importieren | Darf NICHT importieren | Public/Private | Öffentliche Contracts |
|--------|-------------------|------------------|------------------------|----------------|----------------------|
| `setuphelfer.platform` | Version, Health, Capabilities, Runtime-Gate-Hooks, zentrale Bootstrap-Konfiguration | `setuphelfer.core` (Facades, Contracts), `setuphelfer.api` (Router-Typen) | Private Domänen, `backend/cloudserver_*`, `telemetry_server`, `operator_*` | **Public** | `GET /api/version`, `GET /api/health`, Capability-Schemas |
| `setuphelfer.core` | Storage-, Mount-, Safety-Facades; Redaction; gemeinsame Discovery | Standardbibliothek, interne `core/*`-Implementierungen hinter Facades | UI, Rescue-Boot-Kontext, private Server-Module, direkte `subprocess`+`lsblk` außerhalb Allowlist | **Public** | `storage_facade`, `mount_facade`, `safety_facade`, `redaction_contract` |
| `setuphelfer.backup_restore` | Backup-/Restore-/Verify-Orchestrierung, Preflight, Job-State (read-only GETs) | `setuphelfer.core`, `setuphelfer.platform` | Private Lizenz-Enforcement, Cloudserver-Snapshot-Provider | **Public** | `runner_result_contract`, `audit_event_contract`, Backup-Readonly-API |
| `setuphelfer.inspect` | System-/Image-Inspect, lokale Diagnose-Vorbereitung | `setuphelfer.core`, `diagnostic_finding_contract` | Interne Diagnostikserver-Regeln, Operator-APIs | **Public** | `diagnostic_finding_contract`, Inspect-API (plan-only) |
| `setuphelfer.rescue` | Rettungsstick, ISO, Fleet-Session-Stubs, Rescue-Agent-Verträge | `setuphelfer.core`, `setuphelfer.backup_restore` (Preview), `telemetry_client_contract` (opt-in) | `setuphelfer.cloudserver_edition`, Operator-Dashboard, Billing | **Public** | Rescue-Agent-Contracts, `NOTIFICATION_EVENT_CONTRACT` (Rescue-Typen) |
| `setuphelfer.deploy` | Deploy-Runner, Registry, Risk-Gate, Evidence-Routen | `setuphelfer.core`, `setuphelfer.platform`, Deploy-Contracts | Produktions-Infra-Pfade (`deploy/production`), private Operator-Deploy | **Public** | `runner_api_facade`, `runner_result_contract`, Deploy-Write-Runner-Contract |
| `setuphelfer.diagnostics_client` | Lokale `/api/diagnostics/*`, Dev-Diagnostic-Export (redacted) | `setuphelfer.core`, `diagnostic_finding_contract`, `redaction_contract` | `diagnostics_server` (intern), private Matcher-Regeln | **Public** | `diagnostic_finding_contract`, `docs/api/diagnostics_client_contract_openapi.yaml` |
| `setuphelfer.telemetry_client` | Opt-in-Telemetrie-Envelope, lokale Redaction-Preview, Client-Validierung | `setuphelfer.core` (`redaction_contract`, `telemetry_client_contract`) | Telemetrie-Server-Ingest, Signing-Keys, interne Store-APIs | **Public** | `telemetry_client_contract`, `docs/api/telemetry_client_contract_openapi.yaml` |
| `setuphelfer.api` | HTTP-Router, DTO-Mapping, Auth-Grenzen (ohne Fachlogik) | Alle **public** Domänen-Services | Private Module, Geschäftslogik in Routen | **Public** | OpenAPI-Stubs unter `docs/api/` |
| `setuphelfer.frontend` | UI, ViewModels, i18n, Tauri-Shell | Public API-Clients, public Contract-Typen (via OpenAPI/generiert) | `frontend/src/operator/`, CloudOperatorDashboard, private API-Keys | **Public** | Frontend-Status-ViewModel, öffentliche API-Pfade |
| `setuphelfer.dev_dashboard` | Development Control Center (read-only), Fleet-Observability, Evidence-Feed | `dcc_status_facade`, `setuphelfer.platform`, `setuphelfer.rescue` (read-only) | Operator-Dashboard, Billing, interne Telemetrie-Server-Admin | **Public** (Dev/Lab) | DCC-Readonly-Router, `NOTIFICATION_EVENT_CONTRACT` |
| `setuphelfer.cloudserver_edition` | Cloud-Backup, Snapshots, inkrementelle Jobs, DB-Hooks | Public Contracts (`storage_facade`, `safety_facade`, `telemetry_client_contract`) | — (Root private) | **Private** | Nur Stubs/Interfaces im Public-Repo; Implementierung private |
| `setuphelfer.telemetry_server` | Ingest, Store, Aggregation, Operator-Telemetrie-API | Public `telemetry_client_contract`, `redaction_contract` | Public-Repo darf Server-Code nicht importieren | **Private** | Client-Contract-Spiegel; Server-OpenAPI nur privat |
| `setuphelfer.diagnostics_server` | Zentrale Analyse, Session-Plane, interne Matcher, KB-Korrelation | Public `diagnostic_finding_contract`, Audit-/Telemetry-Envelopes | Public-Repo-Implementierung von internen Regeln | **Private** | Plan-only Client-Contract im Public-Repo |
| `setuphelfer.operator_private` | Operator-Dashboard, Lizenz/Billing, HostPilot-Integration, Plesk-Free (später) | Alle public Contracts; private Server-Domänen untereinander | — | **Private** | Keine UI/API im Public-Repo |

---

## Import-Regeln (Kurz)

1. **Public importiert niemals Private.**  
2. **Private importiert Public-Contracts**, nicht umgekehrt.  
3. **Core-Facades** sind die einzige erlaubte Storage-/Mount-/Safety-Oberfläche für neue Module (siehe [`CORE_FACADE_RULES.md`](CORE_FACADE_RULES.md)).  
4. **Plan-only:** Diagnostik- und Telemetrie-Client-Contracts erlauben keine Execute/Repair-Aktionen über öffentliche APIs.

---

## Verwandte Dokumente

- [`MODULE_CONTRACTS.md`](MODULE_CONTRACTS.md) — Contract-Dateien pro Domäne  
- [`PUBLIC_PRIVATE_MODULE_BOUNDARIES.md`](PUBLIC_PRIVATE_MODULE_BOUNDARIES.md) — Public/Private-Trennung  
- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md) — Produkt-/Edition-Matrix  
- [`MODULE_CATALOG_EN.md`](MODULE_CATALOG_EN.md) — Kanonische Module (Ist)

---

## Status-Hinweis

Monolith-Grenzen (`backend/app.py`, `deploy/routes.py`) sind **noch gelb** — diese Tabelle beschreibt **Soll-Grenzen**, nicht abgeschlossene Entkopplung.
