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
| PI-RS-USB-TELEMETRY-001 USB Write + Boot Smoke | GELB | Superseded by PI-RS-USB-MSI-FIX-001 — Stick jetzt **1.10.0.14** |
| TEL-CLOUD-HEALTH-001 IONOS Telemetry Healthcheck | ROT | DNS ok; **TLS error** (`internal error`, no cert); health not reachable; ingest not tested |
| TEL-CLOUD-FIX-001 IONOS/Plesk TLS + Proxy | GELB | DNS split diagnosed; Plesk vhost/cert/proxy pending — **operator_action_required** |
| Beta Registration (public contract) | GRÜN | Architecture + SQL skeleton |
| Telemetry Server beta.0.1 | GELB | Contract/Mock only — cross-repo preview verified via PI-RS-TEL-003 |
| Diagnostics Server beta.0.1 | GELB | DIAG-LAB-003 preview APIs verified from Rescue Stick |
| WordPress Beta Bridge | GELB | Plugin skeleton |
| PI-RS-WT-004 Working Tree Cleanup + Full Gate | GRÜN | `docs/maintenance/PI_RS_WT_004_WORKING_TREE_CLEANUP_FULL_GATE.md` |
| PI-RS-BUILD-001 Payload Build Decision (MSI Retest) | GRÜN | `build_deferred` — Entscheidung dokumentiert, kein Build in diesem Sprint |
| Stick Payload Build | GRÜN | Workspace + physischer Stick **1.10.0.16** |
| PI-RS-USB-MSI-GUI-002 USB Update 1.10.0.15 + GE63 Retest | GELB | USB-Update **ok**; GE63-Boot Session `20260712_111206` — TUI **failed** |
| PI-RS-MSI-RETEST-001A WIP Reconciliation + Readiness | GRÜN | `wip_reconciled` — physischer Stick **1.10.0.14** Payload |
| PI-RS-MSI-RETEST-002 Physical Boot Retest (1.10.0.15) | ROT | Session `20260712_111206_boot` — **`failed`**: TUI zerstört; `x11_starting` trotz MSI-Compat |
| PI-RS-MSI-FIX-001 Console Shield + boot-progress tty1 | GRÜN | SquashFS **1.10.0.14** repacked; Helper + Race-Fix; Content/Secret-Check ok |
| PI-RS-USB-MSI-FIX-001 USB Update + GE63 Boot Retest | GELB | USB **1.10.0.14** geschrieben; Session 20260712_015835 — GUI/openvt defekt |
| PI-RS-MSI-GUI-002 Disable GUI under MSI Compat | GRÜN | SquashFS **1.10.0.15** repacked; GUI gesperrt unter MSI-Compat |
| PI-RS-MSI-GUI-003 TUI Console Isolation (1.10.0.16) | GRÜN | Retest-003/003B **passed** via PI-RS-MSI-AUTO-EVIDENCE-001 Session `20260713_003100_boot` |
| PI-RS-USB-MSI-GUI-002 USB Update 1.10.0.15 + GE63 Retest | GELB | USB **1.10.0.15** ok; GE63-Boot Session `20260712_111206` — TUI **failed** |
| PI-RS-USB-UPDATER-001 Atomic Payload + Version Sync (1.10.0.16) | GRÜN | Updater gehärtet; Stick **1.10.0.16** atomar; keine manuelle Metadatenkorrektur |
| PI-RS-MSI-RETEST-003 Physical Boot Retest | GRÜN | **passed** — Session `20260713_003100_boot`, Payload **1.10.0.20**, Auto-Lab-Evidence |
| PI-RS-MSI-RETEST-003B Late Console Ownership Evidence | GRÜN | **passed** — Late capture 153,8 s, `console_owner=tui`, `lab-auto-result` passed |
| PI-RS-MSI-AUTO-EVIDENCE-001 Unattended MSI Lab Boot | GRÜN | Payload **1.10.0.20**; ~2,5 min Boot→Collect→Shutdown; Evidence importiert + CSE preview ok |
