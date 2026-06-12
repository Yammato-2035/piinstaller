# DCC Nächste Migrationen — Phase F.3

**HEAD:** `8bb910c` · **Status:** Roadmap (kein Refactoring in F.3)

| Priorität | Ziel | Aktion | Risiko | Voraussetzung |
|-----------|------|--------|--------|---------------|
| **P1** | `ai_prompt_generate_stub` | `build_dcc_cursor_meta_prompt_api()` statt direktem `build_dashboard_status` | niedrig | F.2 Facade stabil |
| **P2** | `dev_dashboard_readonly` (E.8) | Facade-Sections für backend-health, notifications, evidence | niedrig | Facade-Section-APIs vorhanden |
| **P3** | `deploy_job_state` Runtime-Gate | `build_dashboard_status_body` aus Facade | mittel | System Status Facade Design |
| **P4** | Roadmap Subrouter | **beibehalten** (`boundary_ok_registry_only`) | niedrig | nur bei Runtime-Overlay ändern |
| **P5** | System Status Facade | `/api/status` aus `app.py` extrahieren | hoch | E.7 blocked extraction |
| **P6** | Network Info Facade | `/api/system/network` extrahieren | hoch | E.7 blocked extraction |
| **P7** | Frontend Status ViewModel | `dccStatusViewModel.ts` zentralisieren | mittel | API-Contracts stabil |
| **P8** | Dev Dashboard Aggregation Facade | weitere `app.py` DCC-Handler | mittel | F.4 Stub + readonly zuerst |

## Empfohlene Reihenfolge

1. **F.4** — `ai_prompt_generate_stub` (kleinster Diff)
2. **F.4** — readonly-Router auf Facade-Sections
3. **F.5** — Deploy-Gate über Facade-Hook
4. **G** — System/Network Facades (separater Track)
5. **H** — Frontend ViewModel

Evidence: [DCC_AGGREGATION_AUDIT_F3.md](DCC_AGGREGATION_AUDIT_F3.md)
