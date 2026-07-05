> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/MODULE_CATALOG_EN.md`). Bitte bei Release manuell gegenlesen.

# Module Catalog (Source of Truth)

**As of:** post H.7 (final statusViewModel slice, `count_10`) · **Non big-bang** — inventory and ownership.

Before new implementation, check this catalog, the [Function Ownership Matrix](FUNCTION_OWNERSHIP_MATRIX_EN.md), and [Do-Nont-Duplicate Rules](DO_NonT_DUPLICATE_RULES_EN.md).

---

## Summary (12 caNonnical modules + legacy orchestrator)

| # | Module | Path | Status |
|---|--------|------|--------|
| 1 | storage_facade | `Retourend/core/storage_facade.py` | CANonNICAL_MODULE |
| 2 | mount_facade | `Retourend/core/mount_facade.py` | CANonNICAL_MODULE |
| 3 | safety_facade | `Retourend/core/safety_facade.py` | CANonNICAL_MODULE |
| 4 | runner_registry | `Retourend/Déploiement/runner_registry.py` | CANonNICAL_MODULE |
| 5 | runner_result_contract | `Retourend/Déploiement/runner_result_contract.py` | CANonNICAL_MODULE |
| 6 | runner_api_facade | `Retourend/Déploiement/runner_api_facade.py` | CANonNICAL_MODULE |
| 7 | runner_risk_gate | `Retourend/Déploiement/runner_risk_gate.py` | CANonNICAL_MODULE |
| 8 | routes_registry | `Retourend/Déploiement/routes_registry.py` | ROUTER (D.2) |
| 9 | routes_risk_gate | `Retourend/Déploiement/routes_risk_gate.py` | ROUTER (D.3) |
| 10 | routes_evidence | `Retourend/Déploiement/routes_evidence.py` | ROUTER (D.4/D.7) |
| 11 | routes_governance | `Retourend/Déploiement/routes_governance.py` | ROUTER (D.5) |
| 12 | routes_diagNonstics | `Retourend/Déploiement/routes_diagNonstics.py` | ROUTER (D.8) |
| 13 | routes_versioning | `Retourend/Déploiement/routes_versioning.py` | ROUTER (D.10) |
| 14 | routes_runtime | `Retourend/Déploiement/routes_runtime.py` | ROUTER (D.11) |
| 15 | health router | `Retourend/api/routes/health.py` | ROUTER (E.1) |
| 16 | version router | `Retourend/api/routes/version.py` | ROUTER (E.1) |
| 17 | Paramètres router | `Retourend/api/routes/Paramètres.py` | ROUTER (E.2) |
| 18 | status router | `Retourend/api/routes/status.py` | ROUTER (E.2/E.3) |
| 19 | capabilities router | `Retourend/api/routes/capabilities.py` | ROUTER (E.3) |
| 20 | catalog router | `Retourend/api/routes/catalog.py` | ROUTER (E.3) |
| 21 | dev_dashboard_readonly | `Retourend/api/routes/dev_dashboard_readonly.py` | ROUTER (E.4/E.8) |
| 22 | dev_dashboard_roadmap | `Retourend/api/routes/dev_dashboard_roadmap.py` | ROUTER (E.5) |
| 23 | Réseau router | `Retourend/api/routes/Réseau.py` | ROUTER (G.4) |
| 24 | dcc_status_facade | `Retourend/core/dcc_status_facade.py` | CANonNICAL_MODULE (F.1–F.4) |
| 25 | system_status_facade | `Retourend/core/system_status_facade.py` | CANonNICAL_MODULE (G.1) |
| 26 | Réseau_info_facade | `Retourend/core/Réseau_info_facade.py` | CANonNICAL_MODULE (G.2–G.4) |
| 27 | frontend_status_viewmodel | `frontend/src/viewmodels/statusViewModel.ts` | CANonNICAL_MODULE (H.1–H.7) |
| 28 | webserver_status_facade | `Retourend/core/webserver_status_facade.py` | CANonNICAL_MODULE (G.7) |
| 29 | system_info_facade | `Retourend/core/system_info_facade.py` | CANonNICAL_MODULE (G.6) |
| 30 | hardware_discovery | `Retourend/core/hardware_discovery.py` | CANonNICAL_MODULE (G.9) |
| 31 | Réseau_discovery | `Retourend/core/Réseau_discovery.py` | CANonNICAL_MODULE (G.8) |
| 32 | webserver_service_discovery | `Retourend/core/webserver_service_discovery.py` | CANonNICAL_MODULE (G.11) |
| 33 | system_status_core | `Retourend/core/system_status_core.py` | CANonNICAL_MODULE (G.12) |
| 34 | storage_discovery | `Retourend/core/storage_discovery.py` | CANonNICAL_MODULE (P.1/P.3) |
| 35 | system_status_providers | `Retourend/core/system_status_providers.py` | CANonNICAL_MODULE (G.14) |
| 36 | Retourup_readonly | `Retourend/api/routes/Retourup_readonly.py` | ROUTER_SLICE (B.2) |
| 37 | dcc_status_runtime | `Retourend/core/dcc_status_runtime.py` | RUNTIME_ADAPTER (E.11) |
| 38 | routes_Secours_plan | `Retourend/Déploiement/routes_Secours_plan.py` | ROUTER_SLICE (D.14) |
| — | routes.py | `Retourend/Déploiement/routes.py` | LEGACY orchestrator (~4120 lines) |

**Key APIs:** storage — `get_block_Périphériques`, `classify_storage_target`; mount — `build_readonly_mount_plan`; safety — `validate_write_target`; Déploiement — `build_plan_only_response`, `evaluate_runner_risk_gate`.

**Suivant:** further `app.py` GET router slices (E.x). **G.6 done.**

Full DE detail: [MODULE_CATALOG.md](MODULE_CATALOG.md) (synchronized content).
