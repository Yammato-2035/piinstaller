# Development Cockpit — Testmatrix

| ID | Bereich | Erwartung | Status | Evidence / Anker |
|----|---------|-----------|--------|-------------------|
| **DEV-001** | **Development Cockpit / Digitale Roadmap** | Read-only API `GET /api/dev-dashboard/*`; keine gefährlichen Schreibaktionen; Platzhalter-POSTs nur `confirm_required` / `not_implemented_safe`; UI nur Experten/Entwickler; **Runtime vs. Workspace** + **`deploy_drift`** (Whitelist + optionales **Deployment-Manifest** `build/deploy/setuphelfer-deploy-manifest.json`, Generator `backend/tools/generate_deploy_manifest.py`) | **Gelb** (kein separater Tauri-Dev-Client produktiv getestet; Smoke-Tests via `renderToStaticMarkup` auf `DevDashboardBody`, **kein** jsdom/`@testing-library` im Projekt) | `docs/dev-dashboard/README.md`, `docs/dev-dashboard/DEV_CLIENT_DE.md`, `DEV_CLIENT_EN.md`, `backend/core/dev_dashboard.py`, `backend/core/deploy_manifest.py`, `frontend/src/pages/DevDashboard.tsx`, `frontend/src/pages/DevDashboardBody.tsx`, `frontend/src/pages/devDashboardFilters.ts`, pytest `test_dev_dashboard_v1.py`, `test_deploy_manifest.py`, Vitest `DevDashboardBody.test.ts`, `devDashboardFilters.test.ts` |

**Abgleich:** `docs/dev-dashboard/modules/backup-restore.json` folgt `BACKUP_RESTORE_TEST_MATRIX.md` / `STATUS_MATRIX.md` / `backup_restore_release_gate.json` (Ampeln nicht widersprüchlich zum Gate; DEV-001 bleibt Gelb).

**Phase 0 (vor produktiven Runtime-/Backup-/HW-Tests):** verbindliche Checkliste in `docs/dev-dashboard/PHASE0_RUNTIME_GATE.md`; Cursor-Regel `.cursor/rules/runtime-phase0-gate.mdc`; Runtime/Paket: **`scripts/check-runtime-deploy-gate.sh`** + `docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md` (**PKG-001**).
