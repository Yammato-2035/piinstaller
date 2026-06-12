# APP Router Slice — Kandidaten E.4

**HEAD (Baseline):** `c36c304` (nach E.3)

## Ausgewählte E.4-Routen

| Route | Funktion | Domain | nutzt bestehendes Modul | Risiko | E.4 geeignet | Grund |
|-------|----------|--------|-------------------------|--------|--------------|-------|
| `GET /api/dev-dashboard/modules` | `dev_dashboard_modules` | dev_dashboard | `core.dev_dashboard.build_modules_list` | low | **ja** | JSON-Module aus `docs/dev-dashboard/modules` |
| `GET /api/dev-dashboard/modules/{id}` | `dev_dashboard_module_detail` | dev_dashboard | `core.dev_dashboard.build_module_detail` | low | **ja** | Einzelmodul, gleiche Core-Funktion |
| `GET /api/dev-dashboard/evidence-index` | `dev_dashboard_evidence_index` | dev_dashboard | `core.dev_dashboard.build_evidence_index` | low | **ja** | Evidence-Buckets über Core-Walker |
| `GET /api/dev-dashboard/manual-command-runs` | `dev_dashboard_manual_command_runs` | dev_dashboard | `core.dev_dashboard_manual_command_runs` | low | **ja** | Evidence-JSON, kein Shell |
| `GET /api/dev-dashboard/recent-evidence` | `dev_dashboard_recent_evidence` | dev_dashboard | `core.dev_dashboard_recent_evidence` | low | **ja** | Feed über Core-Modul |

## Explizit ausgeschlossen

| Route | Grund |
|-------|-------|
| `GET /api/dev-dashboard/status` | Volle DCC-Aggregation |
| `GET /api/dev-dashboard/control-center-summary` | `asyncio.to_thread` + `build_dashboard_status` |
| `GET /api/dev-dashboard/roadmap` | `build_dashboard_status` + Bundle |
| `GET /api/status`, `GET /api/system/network` | subprocess/Netzwerk |
| Rescue/Deploy/Backup/Restore | Domänen-Ausschluss |
