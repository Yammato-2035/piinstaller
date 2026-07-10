# Status Matrix — Master Phase Beta/Telemetry/Rescue

| Bereich | Status | Evidence |
|---------|--------|----------|
| Rescue Package Policy V2 | GRÜN | `docs/evidence/rescue/RESCUE_REQUIRED_PACKAGE_POLICY_V2.json` |
| System Assessment V2 | GRÜN | `backend/core/rescue_system_assessment_v2.py` + Tests |
| Safe Action Engine | GRÜN | `backend/core/rescue_repair_advice_engine_v1.py` |
| Network/Telemetry Connectivity | GRÜN | V2 modules + Frontend panel |
| Telemetry Client V2 | GRÜN | Contract + queue + signing |
| PI-RS-TEL-001 Rescue Lab Send | GRÜN | `backend/core/rescue_lab_telemetry_*` + Tests + Evidence |
| PI-RS-TEL-002 Reachability + Queue Preview | GRÜN | Network gate + offline preview + profile-aware runtime gate |
| PI-RS-TEL-003 Cross-Repo Preview Verification | GRÜN | Rescue → Diagnostics validate/findings preview (localhost lab) |
| Beta Registration (public contract) | GRÜN | Architecture + SQL skeleton |
| Telemetry Server beta.0.1 | GELB | Contract/Mock only — cross-repo preview verified via PI-RS-TEL-003 |
| Diagnostics Server beta.0.1 | GELB | DIAG-LAB-003 preview APIs verified from Rescue Stick |
| WordPress Beta Bridge | GELB | Plugin skeleton |
| PI-RS-WT-004 Working Tree Cleanup + Full Gate | GRÜN | `docs/maintenance/PI_RS_WT_004_WORKING_TREE_CLEANUP_FULL_GATE.md` |
| PI-RS-BUILD-001 Payload Build Decision (MSI Retest) | GRÜN | `build_deferred` — Entscheidung dokumentiert, kein Build in diesem Sprint |
| Stick Payload Build | GELB | Repack auf 1.9.19.4 deferred → PI-RS-MSI-RETEST-001 |
