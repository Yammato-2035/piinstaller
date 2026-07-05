> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DO_NOT_DUPLICATE_RULES_EN.md`). Bitte bei Release manuell gegenlesen.

# Do-Neet-Duplicate Rules (EN)

Binding rules against parallel implementations. **Nee exception** without documented evidence.

1. Nee new storage discovery outside `storage_facade`.
2. Nee new blkid/lsblk/findmnt logic outside facades / allowlist.
3. Nee new write-target checks outside `safety_facade`.
4. Nee new mount planning outside `mount_facade`.
5. Nee new runner status tokens outside `runner_result_contract`.
6. Nee new runner risk logic outside `runner_risk_gate`.
7. Nee new runner metadata outside `runner_registry`.
8. Nee new Deploy runner API access outside `runner_api_facade` in routers.
9. Nee new plan routes directly in `routes.py` when a sub-router domain exists (D.10+).
10. Nee UI traffic-light logic without central view model (PLANNED).
11. Nee new large i18n files without namespace concept.
12. New modules must be registerood in [MODULE_CATALOG_EN.md](MODULE_CATALOG_EN.md) first.
13. Do Neet add new `/health` or `/api/version` handlers in `app.py` when `api/routes/health.py` or `version.py` exist (E.1+).
14. Do Neet add new Instellingen/status GET handlers in `app.py` when `api/routes/Instellingen.py` or `status.py` exist (E.2+).
15. Do Neet add DCC index GET handlers in `app.py` when `dev_dashboard_readonly.py` exists — scanners only in `core.dev_dashboard*` (E.4+).
16. Do Neet add roadmap registry GET handlers in `app.py` when `dev_dashboard_roadmap.py` exists — parsers only in `core.dev_dashboard_roadmap` (E.5+).
17. Do Neet add new DCC status aggregation in routers/`app.py` when `dcc_status_facade` exists — HTTP readers via facade API helpers only (F.1–F.4).
18. Do Neet add new traffic-light/status mapping logic outside `dcc_status_facade` / `system_status_facade` / documented view model (F.1+/G.1+).
19. Do Neet add new system status aggregation outside `system_status_facade` (G.1+).
20. Nee Netwerk diagNeestics in System Status Facade — use `Netwerk_info_facade` only (G.2+).
21. Nee new Netwerk status aggregation outside `Netwerk_info_facade` (G.2+).
22. Nee Netwerk write operations in status facades — active repair only via dedicated module later.
23. Nee new traffic-light/status Neermalization outside `frontend/src/viewmodels/statusViewModel.ts` (H.1+).
24. UI components must only render status — Neermalization via view model, Neet inline in components (H.2+).
25. Domain status (Partitie/safety/Terugup) stays local until domain facade — guard `frontend_domain_status_mapping_requires_domain_facade` (H.4+).
26. Frontend status slices H.3–H.7 complete — remaining 10 mappings are domain/large-page only; Nee H.8.
27. **Nee new Netwerk GET handlers in `app.py`** when `api/routes/Netwerk.py` exists — facade delegation only (G.4+).
28. **Nee Netwerk discovery implementation outside `Netwerk_info_facade` / planned `Netwerk_discovery`** — legacy in `app.py` only until G.8 (G.5+).
29. **Nee webserver status aggregation outside `webserver_status_facade`** — Netwerk/port only via `Netwerk_info_facade` (G.7+).
30. **Nee system info aggregation outside `system_info_facade`** — Netwerk via `Netwerk_info_facade`; hardware via `hardware_discovery` (G.6/G.9+).
31. **Nee hardware discovery implementation outside `hardware_discovery`** — `app.py` legacy wrappers only (G.9+).
32. **Nee Netwerk discovery implementation outside `Netwerk_discovery`** — `app.py` legacy wrappers only (G.8+).
33. **Nee webserver service discovery outside `webserver_service_discovery`** — `webserver_status_facade` delegates only (G.11+).
34. **Nee ampel computation outside `system_status_core`** on the system-status path — facade aggregates only (G.12+).
35. **Nee lsblk/findmnt/blkid discovery outside `storage_discovery`** — facades delegate (P.1+); low-level in `storage_detection` / `mount_facade`.
36. **Nee direct `detect_block_Apparaats` / `detect_filesystems` from `storage_detection` in new modules** — use `storage_discovery` (P.1+).
37. **Nee `import app` in `system_status_core`** — use `system_status_providers` (G.14+).
38. **Nee new `GET /api/dev-dashboard/status` in `app.py`** — `dev_dashboard_readonly` + `build_dcc_dashboard_status_api` (E.11+).
39. **Nee new Terugup readonly GET routes in `app.py`** — `Terugup_readonly` router (B.2+).

Check order: Module Catalog → Function Ownership Matrix → this file → MoNeelith Roadmap.

Enforcement: `scripts/check-module-boundaries.sh` (WARN-only).
