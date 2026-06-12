# DCC Status Aggregation Audit — Phase F.1

**HEAD:** `03fbc09` · **Scope:** Ist-Analyse vor `core.dcc_status_facade`

## DCC-Status-Lieferanten (Core)

| Modul | Funktion | Zweck |
|-------|----------|-------|
| `core.dev_dashboard` | `build_dashboard_status` | **Haupt-Aggregation** — Runtime, Workspace, Deploy-Drift, Cockpit-Enrichment |
| `core.dev_dashboard_status_service` | `build_dev_dashboard_status` | Async-Wrapper + Profil-Gate + Timeout/Degraded |
| `core.dev_dashboard_status_service` | `build_dcc_profile_block_response` | Developer-Capability-Gate (404-Block) |
| `core.dev_dashboard_compact_status` | `build_compact_dcc_status` | Kompakt-Ampel (capability/compact-status Router) |
| `core.dev_dashboard_cockpit` | `enrich_dashboard_cockpit` | Cockpit-Felder an Dashboard-Body |
| `core.dev_dashboard_cockpit` | `build_prompt_findings` | KI-Export-Findings aus Dashboard-Kontext |
| `core.dev_dashboard_cockpit` | `build_cursor_meta_prompt` | Meta-Prompt aus Findings |
| `core.dev_control_center_summary` | `build_control_center_summary` | Control-Center-Übersicht |

## Roadmap-Status

| Modul | Funktion | Zweck |
|-------|----------|-------|
| `core.dev_dashboard_roadmap` | `load_roadmap_registry_bundle` | Registry JSON + optional `dashboard_context` Overlay |
| `core.dev_dashboard_roadmap` | `build_dashboard_roadmap` | Thin-Wrapper → `roadmap` Slice aus Bundle |

Roadmap-native Status: `green`, `yellow`, `red`, `blocked`, `partial_green`, `unknown` (`ALLOWED_STATUS_VALUES`).

## Backend-/Notification-/Evidence-Status

| Modul | Funktion | Zweck |
|-------|----------|-------|
| `core.dev_dashboard_backend_health` | `load_backend_health_snapshot` | Evidence-JSON, Status `ok`/`warning`/`blocked`/`unknown` |
| `core.notification_state` | `build_notification_summary` | Summary-JSON, Ampel `green`/`yellow`/`gray` |
| `core.notification_state` | `list_notification_events` | Event-Liste (read) |
| `core.dev_dashboard` | `build_evidence_index` | Evidence-Buckets unter `docs/evidence` |
| `core.dev_dashboard_recent_evidence` | `build_recent_evidence_feed` | Recent-Evidence-Feed (Router E.4) |
| `core.dev_dashboard_manual_command_runs` | `build_manual_command_runs_index` | Manual-Command-Runs (Router E.4) |

## Routen mit direkter Aggregation in `app.py`

| Route | Aggregation | Blocker |
|-------|-------------|---------|
| `GET /api/dev-dashboard/status` | `build_dev_dashboard_status` → `build_dashboard_status` | Profil-Gate, Backup-Jobs, Timeout |
| `GET /api/dev-dashboard/roadmap` | `build_dashboard_status` + `load_roadmap_registry_bundle(dashboard_context=…)` | Dashboard-Kontext-Pflicht |
| `GET /api/dev-dashboard/control-center-summary` | `build_dashboard_status` + `build_control_center_summary` | DCC Aggregation Facade (F.1+) |
| `GET /api/dev-dashboard/prompt-findings` | `build_dashboard_status` + `build_prompt_findings` | DCC Aggregation Facade |
| `GET /api/dev-dashboard/cursor-meta-prompt` | `build_dashboard_status` + `build_cursor_meta_prompt` | DCC Aggregation Facade |
| `GET /api/dev-dashboard/project-overview` | `build_dashboard_status` + Cockpit | DCC Aggregation Facade |

Bereits extrahiert (ohne `build_dashboard_status` im Router):

- `dev_dashboard_readonly.py` — modules, evidence, backend-health, notifications
- `dev_dashboard_roadmap.py` — Subroutes ohne `dashboard_context`

## Mehrfach vorkommende Status-/Ampel-Felder

| Vokabular | Vorkommen | Facade-Mapping (F.1) |
|-----------|-----------|----------------------|
| `green`/`yellow`/`red`/`gray` | Roadmap, Cockpit, Notifications | → `ok`/`warning`/`blocked`/`unavailable` |
| `ok`/`warning`/`blocked`/`unknown` | Backend-Health | direkt bzw. `build_section_status` |
| `success`/`degraded`/`error` | `build_dev_dashboard_status` API envelope | `ok`/`degraded`/`blocked` |
| `deploy_drift.status`, `consistency.status` | Dashboard-Body | in `normalize_legacy_dcc_status` |

**Abweichung dokumentiert:** Roadmap und Notification behalten **native** Werte in `data`; nur Facade-`section.status` nutzt das einheitliche Set (`ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`).

## Künftig nur über `dcc_status_facade` (Ziel F.2+)

- `build_dashboard_status` aus Routern und `app.py`-Handlern
- `load_roadmap_registry_bundle` mit `dashboard_context` aus HTTP-Schicht
- Parallele `_normalize_ampel` / Status-Mapping in Routern
- Neue DCC-Aggregations-GET ohne Facade-Delegation

Profil-Gate bleibt Owner: `core.dev_dashboard_status_service` (nicht in Facade dupliziert).

## F.1 Ergebnis

Neues Modul: `backend/core/dcc_status_facade.py` — Contract + Delegation, **keine Route-Migration** in F.1.
