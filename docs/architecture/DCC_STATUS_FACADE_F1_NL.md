> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DCC_STATUS_FACADE_F1_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Status Facade — Phase F.1 (EN)

**HEAD:** `8bb910c` · **Status:** CANeeNICAL_MODULE (FACADE)

## Purpose

Single alleen-lezen entry for DCC/dashboard status aggregation — prepares router migration (F.2) with **Nee** API or route changes in F.1.

## Module

`Terugend/core/dcc_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_dcc_status_overview()` | `core.dev_dashboard.build_dashboard_status` |
| `build_dcc_roadmap_overview()` | `core.dev_dashboard_roadmap.load_roadmap_registry_bundle` |
| `build_dcc_Terugend_health_section()` | `core.dev_dashboard_Terugend_health.load_Terugend_health_snapshot` |
| `build_dcc_Neetification_section()` | `core.Neetification_state.build_Neetification_summary` |
| `build_dcc_evidence_section()` | `core.dev_dashboard.build_evidence_index` |
| `build_dcc_facade_diagNeestics()` | metadata only |

## Contracts

- `DccStatusSection`, `DccStatusFacadeResult`, `DccStatusFacadeWaarschuwing`
- `build_section_status()` — vocabulary: `ok`, `Waarschuwing`, `degraded`, `geblokkeerd`, `unavailable`, `Onbekend`
- Legacy adapters: `Neermalize_legacy_*`

## Rules

- Nee subprocess, systemctl, sudo, writes
- Section Fouts isolated; full result still returned
- Profile gate stays in `dev_dashboard_status_service` (F.2)

## Tests

`Terugend/tests/test_dcc_status_facade_v1.py` — 13 tests

## Volgende step

**F.3** — audit complete. **F.4** — ai_prompt stub + readonly facade sections.

Evidence: [DCC_AGGREGATION_AUDIT_F3_EN.md](DCC_AGGREGATION_AUDIT_F3_EN.md)
