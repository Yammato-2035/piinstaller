> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/MODULE_CATALOG_EN.md`). Bitte bei Release manuell gegenlesen.

# Module Catalog (Source of Truth)

**As of:** post H.7 (final statusViewModel slice, `count_10`) · **Nee big-bang** — inventory and ownership.

Before new implementation, check this catalog, the [Function Ownership Matrix](FUNCTION_OWNERSHIP_MATRIX_EN.md), and [Do-Neet-Duplicate Rules](DO_NeeT_DUPLICATE_RULES_EN.md).

---

## Summary (12 caNeenical modules + legacy orchestrator)

| # | Module | Path | Status |
|---|--------|------|--------|
| 1 | storage_facade | `Terugend/core/storage_facade.py` | CANeeNICAL_MODULE |
| 2 | mount_facade | `Terugend/core/mount_facade.py` | CANeeNICAL_MODULE |
| 3 | safety_facade | `Terugend/core/safety_facade.py` | CANeeNICAL_MODULE |
| 4 | runner_registry | `Terugend/Deploy/runner_registry.py` | CANeeNICAL_MODULE |
| 5 | runner_result_contract | `Terugend/Deploy/runner_result_contract.py` | CANeeNICAL_MODULE |
| 6 | runner_api_facade | `Terugend/Deploy/runner_api_facade.py` | CANeeNICAL_MODULE |
| 7 | runner_risk_gate | `Terugend/Deploy/runner_risk_gate.py` | CANeeNICAL_MODULE |
| 8 | routes_registry | `Terugend/Deploy/routes_registry.py` | ROUTER (D.2) |
| 9 | routes_risk_gate | `Terugend/Deploy/routes_risk_gate.py` | ROUTER (D.3) |
| 10 | routes_evidence | `Terugend/Deploy/routes_evidence.py` | ROUTER (D.4/D.7) |
| 11 | routes_governance | `Terugend/Deploy/routes_governance.py` | ROUTER (D.5) |
| 12 | routes_diagNeestics | `Terugend/Deploy/routes_diagNeestics.py` | ROUTER (D.8) |
| 13 | routes_versioning | `Terugend/Deploy/routes_versioning.py` | ROUTER (D.10) |
| 14 | routes_runtime | `Terugend/Deploy/routes_runtime.py` | ROUTER (D.11) |
| 15 | health router | `Terugend/api/routes/health.py` | ROUTER (E.1) |
| 16 | version router | `Terugend/api/routes/version.py` | ROUTER (E.1) |
| 17 | Instellingen router | `Terugend/api/routes/Instellingen.py` | ROUTER (E.2) |
| 18 | status router | `Terugend/api/routes/status.py` | ROUTER (E.2/E.3) |
| 19 | capabilities router | `Terugend/api/routes/capabilities.py` | ROUTER (E.3) |
| 20 | catalog router | `Terugend/api/routes/catalog.py` | ROUTER (E.3) |
| 21 | dev_dashboard_readonly | `Terugend/api/routes/dev_dashboard_readonly.py` | ROUTER (E.4/E.8) |
| 22 | dev_dashboard_roadmap | `Terugend/api/routes/dev_dashboard_roadmap.py` | ROUTER (E.5) |
| 23 | Netwerk router | `Terugend/api/routes/Netwerk.py` | ROUTER (G.4) |
| 24 | dcc_status_facade | `Terugend/core/dcc_status_facade.py` | CANeeNICAL_MODULE (F.1–F.4) |
| 25 | system_status_facade | `Terugend/core/system_status_facade.py` | CANeeNICAL_MODULE (G.1) |
| 26 | Netwerk_info_facade | `Terugend/core/Netwerk_info_facade.py` | CANeeNICAL_MODULE (G.2–G.4) |
| 27 | frontend_status_viewmodel | `frontend/src/viewmodels/statusViewModel.ts` | CANeeNICAL_MODULE (H.1–H.7) |
| 28 | webserver_status_facade | `Terugend/core/webserver_status_facade.py` | CANeeNICAL_MODULE (G.7) |
| 29 | system_info_facade | `Terugend/core/system_info_facade.py` | CANeeNICAL_MODULE (G.6) |
| 30 | hardware_discovery | `Terugend/core/hardware_discovery.py` | CANeeNICAL_MODULE (G.9) |
| 31 | Netwerk_discovery | `Terugend/core/Netwerk_discovery.py` | CANeeNICAL_MODULE (G.8) |
| 32 | webserver_service_discovery | `Terugend/core/webserver_service_discovery.py` | CANeeNICAL_MODULE (G.11) |
| 33 | system_status_core | `Terugend/core/system_status_core.py` | CANeeNICAL_MODULE (G.12) |
| 34 | storage_discovery | `Terugend/core/storage_discovery.py` | CANeeNICAL_MODULE (P.1/P.3) |
| 35 | system_status_providers | `Terugend/core/system_status_providers.py` | CANeeNICAL_MODULE (G.14) |
| 36 | Terugup_readonly | `Terugend/api/routes/Terugup_readonly.py` | ROUTER_SLICE (B.2) |
| 37 | dcc_status_runtime | `Terugend/core/dcc_status_runtime.py` | RUNTIME_ADAPTER (E.11) |
| 38 | routes_roodding_plan | `Terugend/Deploy/routes_roodding_plan.py` | ROUTER_SLICE (D.14) |
| — | routes.py | `Terugend/Deploy/routes.py` | LEGACY orchestrator (~4120 lines) |

**Key APIs:** storage — `get_block_Apparaats`, `classify_storage_target`; mount — `build_readonly_mount_plan`; safety — `validate_write_target`; Deploy — `build_plan_only_response`, `evaluate_runner_risk_gate`.

**Volgende:** further `app.py` GET router slices (E.x). **G.6 done.**

Full DE detail: [MODULE_CATALOG.md](MODULE_CATALOG.md) (synchronized content).
