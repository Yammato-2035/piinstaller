# Development Cockpit — Testmatrix

| ID | Bereich | Erwartung | Status | Evidence / Anker |
|----|---------|-----------|--------|-------------------|
| **DEV-001** | **Development Cockpit / Digitale Roadmap** | Read-only API `GET /api/dev-dashboard/*`; keine gefährlichen Schreibaktionen; Platzhalter-POSTs nur `confirm_required` / `not_implemented_safe`; UI nur Experten/Entwickler | **Gelb** (nicht produktiv vollständig integriert / keine HW-Abnahme) | `docs/dev-dashboard/README.md`, `backend/core/dev_dashboard.py`, `frontend/src/pages/DevDashboard.tsx`, `frontend/src/pages/devDashboardFilters.ts`, pytest `test_dev_dashboard_v1.py`, Vitest `devDashboardFilters.test.ts` |
