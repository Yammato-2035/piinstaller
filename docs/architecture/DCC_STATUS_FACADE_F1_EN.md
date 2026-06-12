# DCC Status Facade — Phase F.1 (EN)

**HEAD:** `03fbc09` · **Status:** CANONICAL_MODULE (FACADE)

## Purpose

Single read-only entry for DCC/dashboard status aggregation — prepares router migration (F.2) with **no** API or route changes in F.1.

## Module

`backend/core/dcc_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_dcc_status_overview()` | `core.dev_dashboard.build_dashboard_status` |
| `build_dcc_roadmap_overview()` | `core.dev_dashboard_roadmap.load_roadmap_registry_bundle` |
| `build_dcc_backend_health_section()` | `core.dev_dashboard_backend_health.load_backend_health_snapshot` |
| `build_dcc_notification_section()` | `core.notification_state.build_notification_summary` |
| `build_dcc_evidence_section()` | `core.dev_dashboard.build_evidence_index` |
| `build_dcc_facade_diagnostics()` | metadata only |

## Contracts

- `DccStatusSection`, `DccStatusFacadeResult`, `DccStatusFacadeWarning`
- `build_section_status()` — vocabulary: `ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`
- Legacy adapters: `normalize_legacy_*`

## Rules

- No subprocess, systemctl, sudo, writes
- Section errors isolated; full result still returned
- Profile gate stays in `dev_dashboard_status_service` (F.2)

## Tests

`backend/tests/test_dcc_status_facade_v1.py` — 13 tests

## Next step

**F.2** — migrate `app.py` handlers (status, roadmap root) to facade.
