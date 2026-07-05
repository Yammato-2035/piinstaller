> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DCC_STATUS_FACADE_F1_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Status Facade — Phase F.1 (EN)

**HEAD:** `8bb910c` · **Status:** CANonNICAL_MODULE (FACADE)

## Purpose

Single lecture seule entry for DCC/dashboard status aggregation — prepares router migration (F.2) with **Non** API or route changes in F.1.

## Module

`Retourend/core/dcc_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_dcc_status_overview()` | `core.dev_dashboard.build_dashboard_status` |
| `build_dcc_roadmap_overview()` | `core.dev_dashboard_roadmap.load_roadmap_registry_bundle` |
| `build_dcc_Retourend_health_section()` | `core.dev_dashboard_Retourend_health.load_Retourend_health_snapshot` |
| `build_dcc_Nontification_section()` | `core.Nontification_state.build_Nontification_summary` |
| `build_dcc_evidence_section()` | `core.dev_dashboard.build_evidence_index` |
| `build_dcc_facade_diagNonstics()` | metadata only |

## Contracts

- `DccStatusSection`, `DccStatusFacadeResult`, `DccStatusFacadeAvertissement`
- `build_section_status()` — vocabulary: `ok`, `Avertissement`, `degraded`, `bloqué`, `unavailable`, `Inconnu`
- Legacy adapters: `Nonrmalize_legacy_*`

## Rules

- Non subprocess, systemctl, sudo, writes
- Section Erreurs isolated; full result still returned
- Profile gate stays in `dev_dashboard_status_service` (F.2)

## Tests

`Retourend/tests/test_dcc_status_facade_v1.py` — 13 tests

## Suivant step

**F.3** — audit complete. **F.4** — ai_prompt stub + readonly facade sections.

Evidence: [DCC_AGGREGATION_AUDIT_F3_EN.md](DCC_AGGREGATION_AUDIT_F3_EN.md)
