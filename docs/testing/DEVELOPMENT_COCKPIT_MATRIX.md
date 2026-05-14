# Development Cockpit — Testmatrix

| ID | Bereich | Erwartung | Status | Evidence / Anker |
|----|---------|-----------|--------|-------------------|
| **DEV-001** | **Development Cockpit / Digitale Roadmap** | Read-only API `GET /api/dev-dashboard/*`; keine gefährlichen Schreibaktionen; Platzhalter-POSTs nur `confirm_required` / `not_implemented_safe`; UI nur Experten/Entwickler | **Gelb** (keine vollständige UI-/HW-/Integrationsabnahme; Smoke-Tests via `renderToStaticMarkup` auf `DevDashboardBody`, **kein** jsdom/`@testing-library` im Projekt) | `docs/dev-dashboard/README.md`, `backend/core/dev_dashboard.py`, `frontend/src/pages/DevDashboard.tsx`, `frontend/src/pages/DevDashboardBody.tsx`, `frontend/src/pages/devDashboardFilters.ts`, pytest `test_dev_dashboard_v1.py`, Vitest `DevDashboardBody.test.ts`, `devDashboardFilters.test.ts` |

**Abgleich:** `docs/dev-dashboard/modules/backup-restore.json` folgt `BACKUP_RESTORE_TEST_MATRIX.md` / `STATUS_MATRIX.md` / `backup_restore_release_gate.json` (Ampeln nicht widersprüchlich zum Gate; DEV-001 bleibt Gelb).
