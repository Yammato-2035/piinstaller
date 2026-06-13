# Do-Not-Duplicate Rules (EN)

Binding rules against parallel implementations. **No exception** without documented evidence.

1. No new storage discovery outside `storage_facade`.
2. No new blkid/lsblk/findmnt logic outside facades / allowlist.
3. No new write-target checks outside `safety_facade`.
4. No new mount planning outside `mount_facade`.
5. No new runner status tokens outside `runner_result_contract`.
6. No new runner risk logic outside `runner_risk_gate`.
7. No new runner metadata outside `runner_registry`.
8. No new deploy runner API access outside `runner_api_facade` in routers.
9. No new plan routes directly in `routes.py` when a sub-router domain exists (D.10+).
10. No UI traffic-light logic without central view model (PLANNED).
11. No new large i18n files without namespace concept.
12. New modules must be registered in [MODULE_CATALOG_EN.md](MODULE_CATALOG_EN.md) first.
13. Do not add new `/health` or `/api/version` handlers in `app.py` when `api/routes/health.py` or `version.py` exist (E.1+).
14. Do not add new settings/status GET handlers in `app.py` when `api/routes/settings.py` or `status.py` exist (E.2+).
15. Do not add DCC index GET handlers in `app.py` when `dev_dashboard_readonly.py` exists — scanners only in `core.dev_dashboard*` (E.4+).
16. Do not add roadmap registry GET handlers in `app.py` when `dev_dashboard_roadmap.py` exists — parsers only in `core.dev_dashboard_roadmap` (E.5+).
17. Do not add new DCC status aggregation in routers/`app.py` when `dcc_status_facade` exists — HTTP readers via facade API helpers only (F.1–F.4).
18. Do not add new traffic-light/status mapping logic outside `dcc_status_facade` / `system_status_facade` / documented view model (F.1+/G.1+).
19. Do not add new system status aggregation outside `system_status_facade` (G.1+).
20. No network diagnostics in System Status Facade — use `network_info_facade` only (G.2+).
21. No new network status aggregation outside `network_info_facade` (G.2+).
22. No network write operations in status facades — active repair only via dedicated module later.
23. No new traffic-light/status normalization outside `frontend/src/viewmodels/statusViewModel.ts` (H.1+).
24. UI components must only render status — normalization via view model, not inline in components (H.2+).
25. Domain status (partition/safety/backup) stays local until domain facade — guard `frontend_domain_status_mapping_requires_domain_facade` (H.4+). Module Catalog → Function Ownership Matrix → this file → Monolith Roadmap.

Enforcement: `scripts/check-module-boundaries.sh` (WARN-only).
