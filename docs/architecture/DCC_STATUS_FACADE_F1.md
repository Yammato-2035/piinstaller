# DCC Status Facade — Phase F.1

**HEAD:** `8bb910c` · **Status:** CANONICAL_MODULE (FACADE)

## Zweck

Einheitlicher read-only Einstieg für DCC-/Dashboard-Statusaggregation — Vorbereitung für Router-Migration (F.2), **ohne** API- oder Route-Änderung in F.1.

## Modul

`backend/core/dcc_status_facade.py` · `FACADE_VERSION = 1`

## Öffentliche API

| Funktion | Delegiert an |
|----------|--------------|
| `build_dcc_status_overview()` | `core.dev_dashboard.build_dashboard_status` |
| `build_dcc_roadmap_overview()` | `core.dev_dashboard_roadmap.load_roadmap_registry_bundle` |
| `build_dcc_backend_health_section()` | `core.dev_dashboard_backend_health.load_backend_health_snapshot` |
| `build_dcc_notification_section()` | `core.notification_state.build_notification_summary` |
| `build_dcc_evidence_section()` | `core.dev_dashboard.build_evidence_index` |
| `build_dcc_facade_diagnostics()` | Metadaten (leichtgewichtig) |

## Contracts

- `DccStatusSection`, `DccStatusFacadeResult`, `DccStatusFacadeWarning`
- `build_section_status()` — Facade-Vokabular: `ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`
- Legacy-Adapter: `normalize_legacy_dcc_status`, `normalize_legacy_roadmap_bundle`, `normalize_legacy_notification_summary`

## Regeln

- Kein subprocess, systemctl, sudo, Schreiboperationen
- Section-Fehler isoliert (`unavailable`), kein Komplettausfall
- Profil-Gate bleibt in `dev_dashboard_status_service` (F.2)

## Tests

`backend/tests/test_dcc_status_facade_v1.py` — 13 Tests

## Nächster Schritt

**F.3** — Audit abgeschlossen. **F.4** — `ai_prompt_generate_stub` + readonly Facade-Sections.

Evidence: [DCC_STATUS_AGGREGATION_AUDIT_F1.md](../evidence/app-monolith/DCC_STATUS_AGGREGATION_AUDIT_F1.md) · [DCC_AGGREGATION_AUDIT_F3.md](DCC_AGGREGATION_AUDIT_F3.md)
