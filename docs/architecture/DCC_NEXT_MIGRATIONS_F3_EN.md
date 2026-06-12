# DCC Next Migrations — Phase F.3

**HEAD:** `8bb910c` · **Status:** Roadmap (no refactoring in F.3)

| Priority | Target | Action | Risk | Prerequisite |
|----------|--------|--------|------|--------------|
| **P1** | `ai_prompt_generate_stub` | Use `build_dcc_cursor_meta_prompt_api()` instead of direct `build_dashboard_status` | low | F.2 facade stable |
| **P2** | `dev_dashboard_readonly` (E.8) | Facade sections for backend-health, notifications, evidence | low | Facade section APIs exist |
| **P3** | `deploy_job_state` runtime gate | `build_dashboard_status_body` from facade | medium | System Status Facade design |
| **P4** | Roadmap subrouter | **keep** (`boundary_ok_registry_only`) | low | change only if runtime overlay needed |
| **P5** | System Status Facade | Extract `/api/status` from `app.py` | high | E.7 blocked extraction |
| **P6** | Network Info Facade | Extract `/api/system/network` | high | E.7 blocked extraction |
| **P7** | Frontend Status ViewModel | Centralize `dccStatusViewModel.ts` | medium | Stable API contracts |
| **P8** | Dev Dashboard Aggregation Facade | Further `app.py` DCC handlers | medium | F.4 stub + readonly first |

## Recommended order

1. **F.4** — `ai_prompt_generate_stub` (smallest diff)
2. **F.4** — readonly router via facade sections
3. **F.5** — deploy gate via facade hook
4. **G** — System/Network facades (separate track)
5. **H** — Frontend ViewModel

Evidence: [DCC_AGGREGATION_AUDIT_F3_EN.md](DCC_AGGREGATION_AUDIT_F3_EN.md)
