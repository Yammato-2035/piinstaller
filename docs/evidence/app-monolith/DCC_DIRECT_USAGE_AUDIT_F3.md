# DCC Direct Usage Audit — Phase F.3

**HEAD:** `8bb910c` · **Scope:** statischer Backend-Scan

## Zusammenfassung

| Bewertung | Anzahl |
|-----------|--------|
| `allowed_canonical` | 10 (facade + core owners) |
| `allowed_core_internal` | 12 |
| `should_use_dcc_status_facade` | 1 |
| `legacy_pending` | 6 |
| `needs_new_facade` | 1 |

## Vollständige Tabelle

| Datei | Funktion | Direktzugriff | Layer | erlaubt? | Grund | Empfehlung |
|-------|----------|---------------|-------|----------|-------|------------|
| `core/dcc_status_facade.py` | Facade-Owner | alle DCC-Core-Calls | Core canonical | **ja** | kanonischer Aggregations-Einstieg | beibehalten |
| `core/dev_dashboard.py` | `build_dashboard_status` | Definition + `build_evidence_index` | Core canonical | **ja** | Low-Level-Owner | nur via Facade aus HTTP |
| `core/dev_dashboard_status_service.py` | `build_dashboard_status_body` | via Facade | Core internal | **ja** | F.2 migriert | beibehalten |
| `core/notification_state.py` | `build_notification_summary` | Owner | Core canonical | **ja** | Notification-State-Owner | Router → Facade-Section (F.4) |
| `core/dev_dashboard_roadmap.py` | `load_roadmap_registry_bundle` | Owner | Core canonical | **ja** | Roadmap-Parser-Owner | Subroutes ohne context OK |
| `core/dev_dashboard_cockpit.py` | `build_prompt_findings` | Cockpit | Core internal | **ja** | Findings-Owner | via Facade-API (F.2 done für GET) |
| `core/dev_control_center_summary.py` | `build_control_center_summary` | Summary-Aggregator | Core internal | **ja** | ruft Roadmap/Evidence intern | HTTP via Facade (F.2) |
| `core/project_overview_dashboard_state.py` | `build_project_overview_dashboard_state` | Multi-Domain | Core internal | **ja** | eigener Overview-State | HTTP via Facade (F.2) |
| `core/deploy_job_state.py` | `build_dashboard_status` | Runtime-Gate | Core internal | **teilweise** | Deploy liest DCC-Runtime | `system_status_facade` oder Facade-Hook (F.4+) |
| `api/routes/dev_dashboard_roadmap.py` | 7 Subroutes | `load_roadmap_registry_bundle()` | HTTP Router | **ja** | Registry-only, kein `dashboard_context` | `boundary_ok_registry_only` |
| `api/routes/dev_dashboard_readonly.py` | backend-health, notifications, evidence | Core direkt | HTTP Router | **legacy** | E.8 vor Facade-Sections | Facade-Section-Delegierung (F.4) |
| `app.py` | `ai_prompt_generate_stub` | `build_dashboard_status` | app.py legacy | **nein** | F.2-Ausnahme | `build_dcc_cursor_meta_prompt_api` (F.4) |
| `app.py` | `ai_prompt_generate_stub` | Cockpit direkt | app.py legacy | **nein** | Duplikat zu GET cursor-meta-prompt | Facade-API nutzen |
| `tests/*` | diverse | Core direkt | Test | **ja** | Unit-Tests gegen Owner | beibehalten |

## F.2 bereits migriert (Referenz)

`status`, `roadmap` (root), `control-center-summary`, `project-overview`, `prompt-findings`, `cursor-meta-prompt` → `dcc_status_facade` API-Helper.
