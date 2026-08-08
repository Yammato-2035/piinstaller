# Status Matrix — Master Phase Beta/Telemetry/Rescue

## PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 — Hauptziele

| Ziel | Status | Evidence / Notes |
|------|--------|------------------|
| A. Autonomous Rescue Diagnostics | `partial` | High-info orchestrator + allowlisted remediation; physical Boot3 pending |
| B. High-Information Boot | `implemented` | `backend/rescue/high_information_boot_orchestrator.py` — fixture-tested; physical pending |
| C. Telemetry Diagnostic Loop | `partial` | Local case builder + spool contracts; IONOS live ACK pending physical |
| D. ASUS Linux Installation | `planned` | Install readiness + dual confirm gates only; **no** internal NVMe write yet |
| E. Persistent Linux Hardware Lab | `planned` | Depends on D + post-install boot evidence |
| F. Driver/Firmware Resolution | `implemented` | Gap engine + intentional profile state; physical validation pending |
| G. Remote Diagnostic Case Correlation | `partial` | Case schema + ranking preview; server correlation pending ACK |
| H. Parallel Agent Development | `implemented` | Scoped agent file lists for 007 foundation |

### Milestones 007

| Milestone | Status | Blockers | Next acceptance |
|-----------|--------|----------|-----------------|
| MILESTONE A — ASUS Autonomous Rescue Diagnostics | `partial` | Boot3 high-info physical | Stages complete + TUI survives Xorg probe fail |
| MILESTONE B — IONOS Telemetry Loop | `blocked` | TLS/proxy historically flaky; need live ACK | `accepted` + `case_id` + forwarding status |
| MILESTONE C — Diagnostic Case Correlation | `partial` | Needs ≥2 high-info boots on same payload | persistent/intermittent/resolved labels |
| MILESTONE D — Linux NVMe Installation | `planned` | Operator dual confirm + readiness=ready | Controlled install on Linux target only |
| MILESTONE E — Persistent ASUS Hardware Lab | `planned` | Depends on D | Boot from Linux NVMe + telemetry |
| MILESTONE F — GPU/NVIDIA Stabilization | `partial` | NVIDIA still profile-disabled until planned test | Separate nouveau/proprietary decision |
| MILESTONE G — Cross-Device Generalization | `planned` | ASUS path first | Reuse orchestrator on non-ASUS |
| MILESTONE H — Raspberry Pi 3–5 Physical Matrix | `planned` | Separate campaign | Physical matrix entries |

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
| PI-RS-MSI-GUI-003 TUI Console Isolation (1.10.0.16) | GELB | Retest-003 **review_required** — Operator TUI ok; Timeline-Lücke |
| PI-RS-USB-MSI-GUI-002 USB Update 1.10.0.15 + GE63 Retest | GELB | USB **1.10.0.15** ok; GE63-Boot Session `20260712_111206` — TUI **failed** |
| PI-RS-USB-UPDATER-001 Atomic Payload + Version Sync (1.10.0.16) | GRÜN | Updater gehärtet; Stick **1.10.0.16** atomar; keine manuelle Metadatenkorrektur |
| PI-RS-MSI-RETEST-003 Physical Boot Retest (1.10.0.16) | GELB | review_required — Operator TUI ok; Timeline ohne tui_mode_selected |
| PI-RS-MSI-RETEST-003B Late Console Ownership Evidence | ROT | Session `20260712_225944_boot` — Capture ~10,5 s; kein console_owner=tui |
| PI-RS-HW-COMPAT-PROVISION-001 Hardware-Erkennung/Treiberauflösung | GELB | `implemented_hardware_inventory_and_provisioning_preview_pending_physical_matrix` — Contracts, Detektoren, Resolver, Katalog, Pi 3-5, 64-GB-Carrier-Plan, OS-Katalog, Read-only-APIs, UI, Telemetrie/DCC, 198+ Unit-Tests grün; **keine** physische Hardware verifiziert |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Memory Baseline Diagnostics | GELB | Early read-only RAM checks + bounded quick probe; keine Langzeitverifikation |
| PI-RS-HW-BASELINE-DIAG-I18N-002 CPU Baseline Diagnostics | GELB | Additive Health-Checks auf `cpu_platform_detection`; keine Stress-Tests |
| PI-RS-HW-BASELINE-DIAG-I18N-002 GPU Baseline Diagnostics | GELB | Read-only GPU-Baseline; red GPU blockiert GUI nicht Backup |
| PI-RS-HW-BASELINE-DIAG-I18N-002 HDD Baseline Diagnostics | GELB | Read-only SMART/Health-Normalizer; kein Self-Test-Autostart |
| PI-RS-HW-BASELINE-DIAG-I18N-002 SATA SSD Baseline Diagnostics | GELB | Read-only SATA-SSD-Baseline; Target-rot nie schreibbar |
| PI-RS-HW-BASELINE-DIAG-I18N-002 NVMe Baseline Diagnostics | GELB | Read-only NVMe-Baseline; Source-rot bleibt backupfähig |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Baseline Gate | GELB | Additive Gate-Schicht; umgeht `safety_facade` nie |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Documentation DE | GELB | `structurally_complete` + `content_reviewed`; `native_review_pending` |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Documentation EN | GELB | `structurally_complete` + `content_reviewed`; `native_review_pending` |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Documentation FR | GELB | `structurally_complete` + `content_reviewed`; `native_review_pending` |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Documentation NL | GELB | `structurally_complete` + `content_reviewed`; `native_review_pending` |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware FAQ DE/EN/FR/NL | GELB | Viersprachige FAQ inkl. Baseline; native Review ausstehend |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Hardware Knowledge Base DE/EN/FR/NL | GELB | KB-Artikelfamilien × 4 Sprachen; native Review ausstehend |
| PI-RS-HW-BASELINE-DIAG-I18N-002 Physical Extended Tests | GELB | `pending_physical_validation` — keine physischen Langzeittests in dieser Phase |
