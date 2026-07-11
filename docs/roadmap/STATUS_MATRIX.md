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
| PI-RS-TEL-004 Cloud Endpoint + beta.v2 Payload Gate | GRÜN | Cloud default `telemetrie.setuphelfer.de`, preview payload v2, auth/reachability gates; send gated; repack deferred |
| PI-RS-TEL-SEND-001 Rescue Stick Cloud Lab Send | GRÜN | `rs.telemetry.lab.v1` Bearer send accepted (`req-fd36496e-…`); gates + Evidence; repack/USB deferred |
| PI-RS-PAYLOAD-TELEMETRY-001 Payload Repack Lab Send | GRÜN | SquashFS **1.10.0.13** lokal gebaut; Lab-Module + Scripts enthalten; Secret-Check ok |
| PI-RS-USB-TELEMETRY-001 USB Write + Boot Smoke | GELB | Stick **1.10.0.13** geschrieben + verify OK; **boot_smoke_operator_action_required** |
| TEL-CLOUD-HEALTH-001 IONOS Telemetry Healthcheck | ROT | DNS ok; **TLS error** (`internal error`, no cert); health not reachable; ingest not tested |
| TEL-CLOUD-FIX-001 IONOS/Plesk TLS + Proxy | GELB | DNS split diagnosed; Plesk vhost/cert/proxy pending — **operator_action_required** |
| Beta Registration (public contract) | GRÜN | Architecture + SQL skeleton |
| Telemetry Server beta.0.1 | GELB | Contract/Mock only — cross-repo preview verified via PI-RS-TEL-003 |
| Diagnostics Server beta.0.1 | GELB | DIAG-LAB-003 preview APIs verified from Rescue Stick |
| WordPress Beta Bridge | GELB | Plugin skeleton |
| PI-RS-WT-004 Working Tree Cleanup + Full Gate | GRÜN | `docs/maintenance/PI_RS_WT_004_WORKING_TREE_CLEANUP_FULL_GATE.md` |
| PI-RS-BUILD-001 Payload Build Decision (MSI Retest) | GRÜN | `build_deferred` — Entscheidung dokumentiert, kein Build in diesem Sprint |
| Stick Payload Build | GRÜN | Stick **1.10.0.13** auf SETUPHELFER geschrieben — Boot-Smoke ausstehend |
| PI-RS-MSI-RETEST-001A WIP Reconciliation + Readiness | GRÜN | `wip_reconciled` — physischer Stick jetzt **1.10.0.13** Payload |
| PI-RS-MSI-RETEST-002 Operator Boot Retest | GELB | Boot **1.10.0.13** auf GE63 — `partial_fail` (TUI overwrite, GUI fail); Root Cause in PI-RS-MSI-FIX-001 |
| PI-RS-MSI-FIX-001 Console Shield + boot-progress tty1 | GRÜN | SquashFS **1.10.0.14** lokal repacked; Helper + Race-Fix; Content/Secret-Check ok; **USB update pending** |
