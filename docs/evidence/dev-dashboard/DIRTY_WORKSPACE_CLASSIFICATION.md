# Dirty Workspace Classification

**Stand:** 2026-05-27 · **HEAD:** `84eb309`  
**Regel:** Kein automatisches Verwerfen, Committen, Formatieren oder Löschen.

## 1 — Dev-Dashboard / Roadmap / Command-Logging (Evidence dieser Aufgabe)

Neu erzeugt und gezielt committbar:

- `docs/evidence/dev-dashboard/RUNTIME_DEPLOY_DRIFT_CLEANUP_*`
- `docs/evidence/dev-dashboard/DIRTY_WORKSPACE_CLASSIFICATION*`
- `docs/evidence/roadmap/ROADMAP_RUNTIME_DRIFT_DELTA*`
- `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.*`
- `docs/roadmap/setuphelfer_roadmap.json`
- `docs/roadmap/setuphelfer_next_prompts.json`
- `docs/dev-dashboard/README.md`, `docs/faq/dev_dashboard_faq.md`, KB, `CHANGELOG.md`

## 2 — Runtime / Deploy-Gate relevant (nicht committen ohne Operator)

| Pfad | Hinweis |
|------|---------|
| `packaging/helpers/setuphelfer-backup-starter.py` | Host-Zeile `/media/setuphelfer` — kann Drift-False-Positive verursachen wenn committed; **nicht** Teil dieses Commits |
| `frontend/public/dev-dashboard.snapshot.json` | Generiert/optional; nicht stagen |

Committed auf `main`, aber **nicht** unter `/opt`: `backend/app.py`, `backend/core/dev_dashboard_manual_command_runs.py`, Cockpit-Frontend — Behebung nur via Deploy-Helper.

## 3 — Unrelated / nicht anfassen

- `VERSION`
- `ckb-next/**`
- Rescue-/Lab-/Handoff-Evidence (`docs/evidence/rescue/*`, `lab-acceptance/*`, `runtime-results/handoff/*`, …)
- `frontend/src/lib/sudoUserMessages.ts`, `Documentation.tsx`, `RaspberryPiConfig.tsx`
- `.cursor/rules/*` (untracked)
- `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_*` (vorherige Session, untracked)

## 4 — Riskant / nur Operator

- `packaging/helpers/setuphelfer-backup-starter.py`
- `packaging/systemd/setuphelfer-backup@.service.d/backup-target.conf.example`
- Jeder `sudo` Deploy / systemd restart

## 5 — Generiert / nicht committen

- `frontend/dist/`, `node_modules/`, `__pycache__`
- `frontend/public/dev-dashboard.snapshot.json` (optional lokal)

JSON: `dirty_workspace_classification_latest.json`
