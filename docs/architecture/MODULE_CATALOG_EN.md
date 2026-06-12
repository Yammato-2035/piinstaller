# Module Catalog (Source of Truth)

**As of:** post E.6 (app.py router slices) · **No big-bang** — inventory and ownership.

Before new implementation, check this catalog, the [Function Ownership Matrix](FUNCTION_OWNERSHIP_MATRIX_EN.md), and [Do-Not-Duplicate Rules](DO_NOT_DUPLICATE_RULES_EN.md).

---

## Summary (12 canonical modules + legacy orchestrator)

| # | Module | Path | Status |
|---|--------|------|--------|
| 1 | storage_facade | `backend/core/storage_facade.py` | CANONICAL_MODULE |
| 2 | mount_facade | `backend/core/mount_facade.py` | CANONICAL_MODULE |
| 3 | safety_facade | `backend/core/safety_facade.py` | CANONICAL_MODULE |
| 4 | runner_registry | `backend/deploy/runner_registry.py` | CANONICAL_MODULE |
| 5 | runner_result_contract | `backend/deploy/runner_result_contract.py` | CANONICAL_MODULE |
| 6 | runner_api_facade | `backend/deploy/runner_api_facade.py` | CANONICAL_MODULE |
| 7 | runner_risk_gate | `backend/deploy/runner_risk_gate.py` | CANONICAL_MODULE |
| 8 | routes_registry | `backend/deploy/routes_registry.py` | ROUTER (D.2) |
| 9 | routes_risk_gate | `backend/deploy/routes_risk_gate.py` | ROUTER (D.3) |
| 10 | routes_evidence | `backend/deploy/routes_evidence.py` | ROUTER (D.4/D.7) |
| 11 | routes_governance | `backend/deploy/routes_governance.py` | ROUTER (D.5) |
| 12 | routes_diagnostics | `backend/deploy/routes_diagnostics.py` | ROUTER (D.8) |
| 13 | routes_versioning | `backend/deploy/routes_versioning.py` | ROUTER (D.10) |
| 14 | routes_runtime | `backend/deploy/routes_runtime.py` | ROUTER (D.11) |
| 15 | health router | `backend/api/routes/health.py` | ROUTER (E.1) |
| 16 | version router | `backend/api/routes/version.py` | ROUTER (E.1) |
| 17 | settings router | `backend/api/routes/settings.py` | ROUTER (E.2) |
| 18 | status router | `backend/api/routes/status.py` | ROUTER (E.2/E.3) |
| 19 | capabilities router | `backend/api/routes/capabilities.py` | ROUTER (E.3) |
| 20 | catalog router | `backend/api/routes/catalog.py` | ROUTER (E.3) |
| 21 | dev_dashboard_readonly | `backend/api/routes/dev_dashboard_readonly.py` | ROUTER (E.4) |
| 22 | dev_dashboard_roadmap | `backend/api/routes/dev_dashboard_roadmap.py` | ROUTER (E.5) |
| — | routes.py | `backend/deploy/routes.py` | LEGACY orchestrator (~4120 lines) |

**Key APIs:** storage — `get_block_devices`, `classify_storage_target`; mount — `build_readonly_mount_plan`; safety — `validate_write_target`; deploy — `build_plan_only_response`, `evaluate_runner_risk_gate`.

**In progress:** `app.py` router slices (E.7+). **Blocked:** `routes_notifications` (D.9 no_safe_slice).

Full DE detail: [MODULE_CATALOG.md](MODULE_CATALOG.md) (synchronized content).
