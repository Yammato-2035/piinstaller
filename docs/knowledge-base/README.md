# Wissensdatenbank (`docs/knowledge-base/`)

Kuratierte Notizen aus Support- und Setup-Runden, damit Lösungen **nicht doppelt** gesucht werden müssen.

| Datei | Inhalt |
|--------|--------|
| [APT_REPOSITORIEN_UND_DOCKER_FAQ.md](APT_REPOSITORIEN_UND_DOCKER_FAQ.md) | **FAQ:** APT-Repositories, Linux Mint vs. Ubuntu-Codename, Docker / Docker Desktop, Grafana, Cursor, Chrome, totes ASUS-Repo, Diagnosebefehle, Copy-Paste-Blöcke |
| [CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md](CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md) | **Session-Protokoll** der zugehörigen Chat-Runde (Verlauf + Verweise, ohne doppelte Befehlslisten) |
| [BACKUP_RECOVERY_FILE_ENGINE_REALITY.md](BACKUP_RECOVERY_FILE_ENGINE_REALITY.md) | **Technik-Notiz:** Schwachstelle `arcname=p.name`, Umstellung auf rekursive relative Pfade, Restore/Verify-Konsistenz, offene Full-Recovery-Risiken |
| [RESTORE_ISOLATED_TEST_FROM_BACKUP.md](RESTORE_ISOLATED_TEST_FROM_BACKUP.md) | **Nachweis:** isolierter `restore_files`-Test nach `/tmp/setuphelfer-restore-test`, Skript `tools/setuphelfer_restore_isolated_test.py`, Grenzen (VM-Archiv, absolute Symlink-Ziele) |
| [BACKUP_TARGET_PERMISSIONS.md](BACKUP_TARGET_PERMISSIONS.md) | **Betrieb:** sicheres Schreibmodell für Backup-Mounts (`setuphelfer`-Gruppe, 0770, systemd `SupplementaryGroups`, optional VM-/Test-Flags) |
| [FULL_RESTORE_BOOT_TEST.md](FULL_RESTORE_BOOT_TEST.md) | **Nachweis (VM):** Datei-Restore, Boot von Zielplatte, SSH-Check; Verweis auf ausführlichen Report; Hinweis auf Installer-Finalzustand |
| [BUILD_RUNTIME_CONSISTENCY.md](BUILD_RUNTIME_CONSISTENCY.md) | **Betrieb/Runtime:** Konsistenz von Source, Build, Tauri, API-Version, Status-Ampeln, Netzwerk- und Update-Start-Verhalten |
| [runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md](runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md) | **Web-UI-Service:** `setuphelfer.service` inactive mit Exit 0 — Hintergrund-`preview` vs. `exec` (Fix `0a1e4a0`); Verweis auf Operations-Doku und Evidence |
| [runtime/systemd-backup-service-backup-targets.md](runtime/systemd-backup-service-backup-targets.md) | **systemd Backup@:** ReadWritePaths und Zielpfade |
| [INSTALLATION_PATH_AUDIT.md](INSTALLATION_PATH_AUDIT.md) | **Audit-Leitfaden:** Pfadmigration, Legacy-Erkennung, funktionale Regeln und erwartete Audit-Ausgaben |
| [BACKUP_VERIFY_PREVIEW_RUNTIME.md](BACKUP_VERIFY_PREVIEW_RUNTIME.md) | **Betrieb/VM-Tests:** `MemoryMax`/OOM, `TMPDIR`/PrivateTmp/ENOSPC bei Verify & Restore-Preview, Deep-Verify-Integrität (Symlinks/Staging), VBox-VDI-Resize + `growpart` |
| [inspect/INSPECT_PHASE_0_1_DE.md](inspect/INSPECT_PHASE_0_1_DE.md) | **Inspect (DE):** Defensive Analyse in Phase 0/1, Rohdatenmodell, keine Schreiboperationen |
| [inspect/INSPECT_PHASE_0_1_EN.md](inspect/INSPECT_PHASE_0_1_EN.md) | **Inspect (EN):** Defensive phase 0/1 baseline, raw-data scope, no write operations |
| [inspect/INSPECT_PHASE_2_CIAO_AND_CLASSIFICATION.md](inspect/INSPECT_PHASE_2_CIAO_AND_CLASSIFICATION.md) | **Inspect Phase 2:** CIAO (interpret/advise), Klassifikationslogik, Risiken falscher Einordnung |
| [../inspect/INSPECT_PHASE_2_DE.md](../inspect/INSPECT_PHASE_2_DE.md) | **Inspect Phase 2 (DE):** API-Felder `classification` / `advice` |
| [../inspect/INSPECT_PHASE_2_EN.md](../inspect/INSPECT_PHASE_2_EN.md) | **Inspect Phase 2 (EN):** API fields `classification` / `advice` |
| [safety/WRITE_SAFETY_OVERVIEW.md](safety/WRITE_SAFETY_OVERVIEW.md) | **Write-Safety:** Zweck, Blockregeln, kein Override in Phase 1 |
| [preflight/PREFLIGHT_BACKUP_OVERVIEW.md](preflight/PREFLIGHT_BACKUP_OVERVIEW.md) | **Preflight Backup:** Zweck, Token-Bestätigung, Hard-Stop-Zielprüfung |

**Verwandt im Repo:** [ASUS ROG Lüftersteuerung](../ASUS_ROG_FAN_CONTROL.md) (Link in die APT-FAQ).

Neue Themen: eigene Datei unter `knowledge-base/` oder Abschnitt in der APT-FAQ ergänzen.

| [rescue/RESCUE_ORCHESTRATOR_PREVIEW.md](rescue/RESCUE_ORCHESTRATOR_PREVIEW.md) | **Rescue Preview:** Safety/Verify/Dryrun-Orchestrierung ohne Execute in Phase 1 |
| [../rescue-stick/RESCUE_RESTORE_PREVIEW_HANDOFF_2026-05-20.md](../rescue-stick/RESCUE_RESTORE_PREVIEW_HANDOFF_2026-05-20.md) | **Rettungsstick C.4:** Restore-Preview-Plan, kanonische Dryrun/Verify-Referenz, kein Restore |
| [../rescue-stick/BACKUP_BEFORE_OVERWRITE_GATE_2026-05-20.md](../rescue-stick/BACKUP_BEFORE_OVERWRITE_GATE_2026-05-20.md) | **Backup-before-overwrite:** Gate vor Restore-Preview bei belegten Zielen |

| [rescue/RESCUE_ORCHESTRATOR_EXECUTE.md](rescue/RESCUE_ORCHESTRATOR_EXECUTE.md) | **Rescue Execute:** Preview-Session-Gate, Token, Re-Checks vor Restore |
| [rescue/POST_RESTORE_VALIDATION.md](rescue/POST_RESTORE_VALIDATION.md) | **Post-Restore Validation:** Read-only Plausibilitätsprüfung nach Restore, ohne Boot-Repair/Auto-Install |
| [boot/BOOT_CAPABILITY_CHECK.md](boot/BOOT_CAPABILITY_CHECK.md) | **Boot Capability Check:** Defensive read-only Plausibilitätsbewertung von Boot-Artefakten |
| [boot/BOOT_REPAIR_PLAN.md](boot/BOOT_REPAIR_PLAN.md) | **Boot Repair Plan:** Strukturierte, rein theoretische Reparaturvorschläge mit Risiko-Codes |
| [rescue/RESCUE_REPORT.md](rescue/RESCUE_REPORT.md) | **Rescue Report:** Aggregierter Recovery-Gesamtbericht mit Risiken, Blockierungen und Next Steps |
| [boot/BOOT_REPAIR_EXECUTE.md](boot/BOOT_REPAIR_EXECUTE.md) | **Boot Repair Execute:** Session-/Token-gebundene Einzelaktionen mit Pre-/Post-Checks |
| [recovery/RECOVERY_MINIMAL_PLAN.md](recovery/RECOVERY_MINIMAL_PLAN.md) | **Recovery Minimal Plan:** Advisory-Plan für minimal erreichbares Recovery-Ziel ohne Ausführung |
| [recovery/RECOVERY_MINIMAL_EXECUTE_PREP.md](recovery/RECOVERY_MINIMAL_EXECUTE_PREP.md) | **Recovery Minimal Execute Prep:** Session-/Token-/Plan-Bindung ohne reale Ausführung |
| [recovery/RECOVERY_MINIMAL_EXECUTE_PHASE_2B.md](recovery/RECOVERY_MINIMAL_EXECUTE_PHASE_2B.md) | **Recovery Minimal Execute 2b:** Strikt begrenzte Einzelaktionen mit target-path containment |
| [recovery/RECOVERY_ACTIVATION_PLAN.md](recovery/RECOVERY_ACTIVATION_PLAN.md) | **Recovery Activation Plan:** Defensiver Aktivierungsplan für Erreichbarkeit ohne Ausführung |
| [recovery/RECOVERY_ACTIVATION_EXECUTE_PREP.md](recovery/RECOVERY_ACTIVATION_EXECUTE_PREP.md) | **Recovery Activation Execute Prep:** Session-/Token-/Plan-Validierung ohne echte Aktivierung |
| [recovery/RECOVERY_ACTIVATION_CONTROLLED_EXECUTE.md](recovery/RECOVERY_ACTIVATION_CONTROLLED_EXECUTE.md) | **Recovery Activation Controlled Execute:** Strikt begrenzte Aktivierungsaktionen mit Single-Use-Session und Fail-Fast |
| [recovery/LAPTOP_FAILURE_TEST_CHAIN.md](recovery/LAPTOP_FAILURE_TEST_CHAIN.md) | **Laptop Failure Test Chain:** Operator-Reihenfolge Backup→Verify→Preview→Runtime-Evidence; Final-Gate ohne Device-Write |
| [recovery/LAPTOP_LIVE_PROBE_EXECUTION_HANDOFF.md](recovery/LAPTOP_LIVE_PROBE_EXECUTION_HANDOFF.md) | **Laptop Live Probe Handoff:** Plan/Execute/Final-Gate mit read-only HTTP, ohne Restore und ohne echte Verify-Pfade ohne Flag |
| [recovery/RESCUE_STICK_BUILD_PREPARATION.md](recovery/RESCUE_STICK_BUILD_PREPARATION.md) | **Rescue Stick Build Preparation:** Architektur-/Gate-Strang, Debian-Live-Plan, ISO-Testmatrix, kein USB/dd in dieser Phase |
| [recovery/RESCUE_ISO_BUILD_AND_VM_VALIDATION.md](recovery/RESCUE_ISO_BUILD_AND_VM_VALIDATION.md) | **Rescue ISO Build & VM Validation:** ISO unter `build/rescue/output/`, VM-QEMU-Checks, readonly HTTP-Probe, kein USB-Restore |
| [recovery/RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION.md](recovery/RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION.md) | **Rescue Live Runtime & Storage:** Discovery, readonly-Mounts, EFI-Analyse, Evidence-Export, Remote-Hilfe-Prep, Safety-Gate |
| [recovery/RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION.md](recovery/RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION.md) | **Rescue Recovery-Simulation:** Szenario-Matrix, Zielvalidierung, Backup-Verify, Restore-Preview, Hardware-Kette, Final-Gate |
| [recovery/RESCUE_ISO_READINESS_PIPELINE.md](recovery/RESCUE_ISO_READINESS_PIPELINE.md) | **Rescue ISO Readiness Pipeline:** Baseline, Layout, Offline-Runtime, Bootflow-Simulation, Safety, Final-Gate, Build-Plan ohne ISO-Write |
| [recovery/RESCUE_ISO_ARTIFACT_PREPARATION.md](recovery/RESCUE_ISO_ARTIFACT_PREPARATION.md) | **Rescue ISO Artefakt-Vorbereitung:** Simuliertes RootFS, Manifeste, geplante Boot-Struktur, Overlay-JSON, Readiness-Gate; kein ISO-Build |
| [recovery/RESCUE_PSEUDO_BOOT_INTEGRATION.md](recovery/RESCUE_PSEUDO_BOOT_INTEGRATION.md) | **Rescue Pseudo-Boot:** Simulierte Bootkette, Service-Startup-JSON, Overlay-Boot, Backend-Health-Static-Scan, Safety/Final-Gate; keine VM |
| [recovery/RESCUE_RUNTIME_ASSEMBLY_PIPELINE.md](recovery/RESCUE_RUNTIME_ASSEMBLY_PIPELINE.md) | **Rescue Runtime Assembly:** `build/rescue/runtime/` Layout, Backend/Frontend/Recovery-Manifeste, Offline-Config, Template-Skripte, Final-Gate; kein ISO/VM |
| [recovery/RESCUE_RUNTIME_BUNDLE_MANIFEST.md](recovery/RESCUE_RUNTIME_BUNDLE_MANIFEST.md) | **Rescue Runtime Bundle:** Inventar, SHA256-Manifest, Seal, Konsistenz-Check; hashbar ohne ISO/Signatur-PKI |
| [recovery/RESCUE_DEBIAN_LIVE_BUILD_INPUTS.md](recovery/RESCUE_DEBIAN_LIVE_BUILD_INPUTS.md) | **Debian Live Build Inputs:** Verzeichnislayout, Paketliste, Includes-Platzhalter, GRUB-/Hook-Templates, Safety/Final-Gate; kein live-build/ISO in dieser Phase |
| [recovery/RESCUE_DRY_BUILD_ORCHESTRATION.md](recovery/RESCUE_DRY_BUILD_ORCHESTRATION.md) | **Rescue Dry Build Orchestration:** Stage-Graph, Input-/Paketaufloesung, Build-Order, Simulationslauf, Final-Gate; read-only, kein ISO/VM |
| [recovery/RESCUE_BUILD_SANDBOX_PREPARATION.md](recovery/RESCUE_BUILD_SANDBOX_PREPARATION.md) | **Rescue Build Sandbox:** Verzeichnislayout, Config-/Runtime-Copy-Plaene, Overlay-/Cleanup-Metadaten, Safety/Final-Gate; kein Mount/Build |
| [recovery/RESCUE_SANDBOX_CONTROLLED_COPY.md](recovery/RESCUE_SANDBOX_CONTROLLED_COPY.md) | **Rescue Sandbox Controlled Copy:** Ausfuehrung der Copy-Plaene nur unter `build/rescue/sandbox/`, SHA256-Verify, Seal, Final-Gate; kein ISO/Build |
| [recovery/RESCUE_BUILD_ENVIRONMENT_EMULATION.md](recovery/RESCUE_BUILD_ENVIRONMENT_EMULATION.md) | **Rescue Build Environment Emulation:** Debian-Live-Build-Umgebung simuliert (Snapshot, Workspace, Outputs-Metadaten, Logs, Overlay); kein live-build/ISO |
| [deploy/DEPLOY_PLAN.md](deploy/DEPLOY_PLAN.md) | **Deploy-Plan:** Neuaufsetzen ohne nutzbares Backup — nur Analyse, keine Installation/Schreibzugriffe |
| [deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md](deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md) | **Betrieb:** Workspace → `/opt/setuphelfer` via `deploy-to-opt.sh`; fehlende Backend-Module, Post-Deploy-Verify, Manifest-Whitelist (ohne DCC/Dev-Server) |
| [CHAT_ZUSAMMENFASSUNG_DEPLOY_TO_OPT_2026-06.md](CHAT_ZUSAMMENFASSUNG_DEPLOY_TO_OPT_2026-06.md) | **Session-Protokoll:** Deploy-to-opt Runtime-Sync-Fix (Verlauf + Verweise) |
| [deploy/DEPLOY_EXECUTE_PREP.md](deploy/DEPLOY_EXECUTE_PREP.md) | **Deploy Execute Prep:** Session-/Token-/Plan-/Profil-Bindung mit NO-OP-Readiness, ohne Installation |
| [deploy/DEPLOY_PREVIEW.md](deploy/DEPLOY_PREVIEW.md) | **Deploy Preview:** Sessiongebundene Deploy-Simulation ohne Schreib-/Installationsaktionen |
| [deploy/DEPLOY_SOURCE_REGISTRY.md](deploy/DEPLOY_SOURCE_REGISTRY.md) | **Deploy Source Registry:** Quellenkatalog mit Metadaten- und Kompatibilitätsbewertung ohne Downloads/Installationen |
| [deploy/DEPLOY_CACHE_PLAN.md](deploy/DEPLOY_CACHE_PLAN.md) | **Deploy Cache Plan:** Download-/Cache-Strategie als reiner Plan ohne Netzwerk/Schreibzugriff |
| [deploy/DEPLOY_CACHE_EXECUTE_LOCAL.md](deploy/DEPLOY_CACHE_EXECUTE_LOCAL.md) | **Deploy Cache Execute Local-only:** Sessiongebundene lokale Cache-Übernahme mit Checksum-/Pfadschutz |
| [deploy/DEPLOY_IMAGE_INSPECT.md](deploy/DEPLOY_IMAGE_INSPECT.md) | **Deploy Image Inspect:** Read-only Metadatenpruefung gecachter Images (Pfad/Datei/Checksum) ohne Mount |
| [deploy/DEPLOY_WRITE_PLAN.md](deploy/DEPLOY_WRITE_PLAN.md) | **Deploy Write Plan:** Vollstaendige Write-Simulation mit Safety-Recheck, ohne Schreiboperation |
| [deploy/DEPLOY_WRITE_EXECUTE_DRYRUN.md](deploy/DEPLOY_WRITE_EXECUTE_DRYRUN.md) | **Deploy Write Execute Dry-Run:** Finale Session-/Token-gebundene Ausfuehrungssimulation ohne Device-Write |
| [deploy/DEPLOY_FINAL_CONFIRMATION.md](deploy/DEPLOY_FINAL_CONFIRMATION.md) | **Deploy Final Confirmation:** Snapshot/Fingerprint-gebundener Letztcheck vor spaeterem Real-Write |
| [deploy/DEPLOY_WRITE_TEST_HARNESS.md](deploy/DEPLOY_WRITE_TEST_HARNESS.md) | **Deploy Write Test Harness:** Isolierte Byte-Copy-Tests nur auf erlaubten Testdateien |
| [deploy/DEPLOY_REAL_WRITE_GUARD.md](deploy/DEPLOY_REAL_WRITE_GUARD.md) | **Deploy Real Write Guard:** Read-only Blockdevice-Guardschicht vor spaeterem echten Schreiben |
| [deploy/DEPLOY_HARDWARE_GATE.md](deploy/DEPLOY_HARDWARE_GATE.md) | **Deploy Hardware Gate:** Read-only Physik-/Medien-Gate mit Operator-Checkliste |
| [deploy/DEPLOY_WRITE_RUNNER_CONTRACT.md](deploy/DEPLOY_WRITE_RUNNER_CONTRACT.md) | **Deploy Write Runner Contract:** Jobfile/Hash/Dry-Run-CLI fuer privilegierten One-Shot-Runner (ohne Write in Phase 1) |
| [deploy/DEPLOY_RUNNER_LIFECYCLE.md](deploy/DEPLOY_RUNNER_LIFECYCLE.md) | **Deploy Runner Lifecycle:** State-Machine, Lockfiles, TOCTOU-Rechecks, Audit, Dry-run-Flow ohne Device-Write |
| [deploy/DEPLOY_RUNNER_HANDOFF.md](deploy/DEPLOY_RUNNER_HANDOFF.md) | **Deploy Runner Handoff:** Sichere Backend->Runner Uebergabe mit atomischem Jobfile-Write, Dry-run-Start und Ergebnisauswertung |
| [deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY.md](deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY.md) | **Deploy Runner Permission Boundary:** Read-only Audit fuer sudoers/env/path/jobdir ohne Rechteaenderung oder Privilegstart |
| [deploy/DEPLOY_RUNNER_SANDBOX.md](deploy/DEPLOY_RUNNER_SANDBOX.md) | **Deploy Runner Sandbox:** Simuliertes Sandbox-Prozessmodell mit ENV-/STDIO-/Timeout-/Recovery-Policies (read-only) |
| [deploy/DEPLOY_RUNNER_INSTALL_PLAN.md](deploy/DEPLOY_RUNNER_INSTALL_PLAN.md) | **Deploy Runner Install Plan:** Read-only Installations-/Betriebsplan fuer spaetere privilegierte Integration |
| [deploy/DEPLOY_RUNNER_INSTALL_VALIDATOR.md](deploy/DEPLOY_RUNNER_INSTALL_VALIDATOR.md) | **Deploy Runner Install Validator:** Read-only Dry-run-Validierung fuer manuelle spaetere Installation |
| [deploy/DEPLOY_RUNNER_PACKAGE_BLUEPRINT.md](deploy/DEPLOY_RUNNER_PACKAGE_BLUEPRINT.md) | **Deploy Runner Package Blueprint:** Read-only Paket-/Installations-Blueprint mit Manifesten und Rollback-Plan |
| [deploy/DEPLOY_RUNNER_INSTALL_CONSISTENCY.md](deploy/DEPLOY_RUNNER_INSTALL_CONSISTENCY.md) | **Deploy Runner Install Consistency:** Read-only Cross-Validation zwischen Plan, Validator und Blueprint |
| [deploy/DEPLOY_RUNNER_RELEASE_READINESS.md](deploy/DEPLOY_RUNNER_RELEASE_READINESS.md) | **Deploy Runner Release Readiness:** Read-only Matrix fuer Komponentenstatus, Risiken und Release-Gaps |
| [deploy/DEPLOY_RUNNER_LAB_READINESS_PLAN.md](deploy/DEPLOY_RUNNER_LAB_READINESS_PLAN.md) | **Deploy Runner Lab Readiness Plan:** Read-only Unblock-Plan fuer blockierende Lab-Readiness-Gaps |
| [deploy/DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN.md](deploy/DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN.md) | **Deploy Runner Sudoers Runtime Test Plan:** Read-only Testdesign fuer manuelle Runtime-Policy-Pruefung |
| [deploy/DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN.md](deploy/DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN.md) | **Deploy Runner Privileged Validation Test Plan:** Read-only Dry-run-Validierungsdesign fuer privilegierten Runner |
| [deploy/DEPLOY_RUNNER_REAL_WRITE_HARDWARE_E2E_TEST_PLAN.md](deploy/DEPLOY_RUNNER_REAL_WRITE_HARDWARE_E2E_TEST_PLAN.md) | **Deploy Runner Real Write HW E2E Test Plan:** Read-only Testdesign fuer spaeteren Hardware-E2E-Write auf Wegwerfmedium |
| [deploy/DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN.md](deploy/DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN.md) | **Deploy Runner Failure Injection HW Test Plan:** Read-only Failure-Injection-Testdesign fuer Hardware-Lab |
| [deploy/DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN.md](deploy/DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN.md) | **Deploy Runner Device Reenumeration Test Plan:** Read-only Testdesign fuer Device-Identity-/Path-Wechsel unter Hardwarebedingungen |
| [deploy/DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN.md](deploy/DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN.md) | **Deploy Runner Hotplug Race Test Plan:** Read-only Testdesign fuer Hotplug-/Unmount-Race-Fehlerpfade |
| [deploy/DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN.md](deploy/DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN.md) | **Deploy Runner Rollback Runtime Test Plan:** Read-only Testdesign fuer sicheres Rollback auf Testartefakten |
| [deploy/DEPLOY_RUNNER_LAB_READINESS_STATUS.md](deploy/DEPLOY_RUNNER_LAB_READINESS_STATUS.md) | **Deploy Runner Lab Readiness Status:** Read-only Statusmodell fuer Testdesign-ready vs. offene Runtime-Ausfuehrung |
| [deploy/DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE.md](deploy/DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE.md) | **Deploy Runner Runtime Runbook Bundle:** Read-only Buendelung aller manuellen Runtime-Runbooks mit Operator-Checklist |
| [deploy/DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT.md](deploy/DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT.md) | **Deploy Runner Runtime Runbook Export:** Read-only Exportpaket fuer Master-Runbook, Checklisten, Templates und Schema |
| [deploy/DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR.md](deploy/DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR.md) | **Deploy Runner Runtime Result Validator:** Read-only Ingestion-Validator fuer Runtime-Ergebnisdateien (Schema/Sequence/Evidence/Acceptance) |
| [deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR.md](deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR.md) | **Deploy Runner Lab Acceptance Aggregator:** Read-only Abnahmeaggregation fuer validierte Runtime-Ergebnisse |
| [deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_REPORT_EXPORT.md](deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_REPORT_EXPORT.md) | **Deploy Runner Lab Acceptance Report Export:** Read-only Export von Lab-Abnahmebericht (DE/EN/JSON + Summaries) |
| [deploy/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION.md](deploy/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION.md) | **Deploy Runner Lab Phase Consolidation:** Finale Read-only Konsolidierung der gesamten Lab-Phase |
| [deploy/DEPLOY_RUNNER_NEXT_PHASE_GATE.md](deploy/DEPLOY_RUNNER_NEXT_PHASE_GATE.md) | **Deploy Runner Next Phase Gate:** Read-only Entscheidungs-Gate fuer die naechste zulaessige Entwicklungsphase |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK.md) | **Deploy Runner Manual Runtime Precheck:** Read-only Startbereitschaftspruefung fuer manuelle Runtime-Runbooks |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE.md) | **Deploy Runner Manual Runtime Result Template:** Read-only Generator fuer leere Runtime-Ergebnisdateien |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_EDIT_CHECKER.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_EDIT_CHECKER.md) | **Deploy Runner Manual Runtime Result Edit Checker:** Read-only Vorpruefung vor harter Ingestion-Validierung |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECKER.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECKER.md) | **Deploy Runner Manual Runtime Result Bundle Checker:** Read-only Bundle-Vorpruefung fuer alle sieben Runtime-Ergebnisdateien |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_GATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_GATE.md) | **Deploy Runner Manual Runtime Result Validator Handoff Gate:** Manifest und Pfad-Revalidation nach Bundle-Ready |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_FROM_HANDOFF.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_FROM_HANDOFF.md) | **Deploy Runner Manual Runtime Result Validator Dry-Run from Handoff:** Validator-Dryrun nur aus Handoff-Manifest |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_REPORT_SEAL.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_REPORT_SEAL.md) | **Validator Report Seal:** SHA256-Seal fuer ok-Dryrun-Report |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX.md) | **Validator Seal Index:** Read-only Index fuer handoff-Seals |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_CONSISTENCY_AUDIT.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_CONSISTENCY_AUDIT.md) | **Validator Seal Consistency Audit:** Index vs. Dateien und SHA256 |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE.md) | **Manual Runtime Evidence Timeline:** Handoff-Artefakte zeitlich aggregiert |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT.md) | **Evidence Final Snapshot:** Timeline-Datei festgehalten |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_ACCEPTANCE_GATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_ACCEPTANCE_GATE.md) | **Final Evidence Acceptance Gate:** Snapshot + Timeline SHA256, nur Acceptance-JSON |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_EXPORT_PACKAGE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_EXPORT_PACKAGE.md) | **Final Evidence Export Package:** Vollstaendige Kette mit SHA256 je Datei exportiert |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX.md) | **Failure Injection Matrix:** Kontrollierte reversible Stoerfaelle fuer reale Testhardware |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW.md) | **Failure Execution Preview:** Manuelle Preview-Laeufe aus der Matrix mit Evidence-Plan |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS.md) | **Failure Operator Checklists:** Schrittbasierte Operator-Gates mit Abort- und Evidence-Regeln |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS.md) | **Failure Test Sessions:** Manuelle Sessions aus Checklisten mit Endzustands-Erwartung |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_RESULT_CAPTURE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_RESULT_CAPTURE.md) | **Failure Test Result Capture:** Manuelle Ergebnisfelder pro Session fuer Evidence und Abweichungen |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_RESULT_EVALUATION.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_RESULT_EVALUATION.md) | **Failure Result Evaluation:** Read-only Abgleich Ergebnisse vs Preview und Sessions |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE.md) | **Failure Readiness Gate:** Pipeline-Vollstaendigkeit und Safety vor Hardwaretests |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTOR.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTOR.md) | **Laptop Failure Run Selector:** Read-only Auswahl manueller Testläufe nach Readiness, ohne Runtime/Execute |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER.md) | **Laptop Failure Operator Runorder:** Read-only Schrittfolge aus Run-Selection für manuelle Abarbeitung |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE.md) | **Laptop Failure Execution Log Template:** Leeres manuelles Ausfuehrungsprotokoll aus der Runorder |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATOR.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATOR.md) | **Laptop Failure Execution Log Validator:** Read-only Pruefung des ausgefuellten Execution-Logs |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY.md) | **Laptop Failure Test Summary:** Read-only Gesamtbewertung aus der Execution-Log-Validierung |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT.md) | **Laptop Failure Final Report:** Finaler Read-only Abschlussbericht aus dem Test-Summary |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE.md) | **Laptop Failure Final Export Package:** Read-only Paket mit Final-Report, Summary, Validation und Execution-Log |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE.md) | **Laptop Failure Evidence Timeline:** Chronologische Read-only Timeline aller Laptop-Failure-Artefakte |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT.md) | **Laptop Failure Final Snapshot:** Hash-gebundener Timeline-Abschluss als Read-only Snapshot |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_GATE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_GATE.md) | **Laptop Failure Final Acceptance Gate:** Read-only Acceptance mit Snapshot-Revalidierung |
| [deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE.md](deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE.md) | **Laptop Failure Finalized Export Package:** Abschließendes Read-only Artefaktpaket mit SHA256 je Datei |
| [deploy/DEPLOY_VERSION_GOVERNANCE.md](deploy/DEPLOY_VERSION_GOVERNANCE.md) | **Version Governance:** Verbindliche SemVer-Regeln und Phasen-Tracking fuer STRICT-Mode |
| [deploy/DEPLOY_VERSION_SOURCE_OF_TRUTH.md](deploy/DEPLOY_VERSION_SOURCE_OF_TRUTH.md) | **Version Source of Truth:** Zentrale Versionsquelle + Drift-Pruefung fuer Backend/Frontend/Tauri/API/Evidence |
| [deploy/DEPLOY_SETUPHELFER_IDENTIFIER_MIGRATION.md](deploy/DEPLOY_SETUPHELFER_IDENTIFIER_MIGRATION.md) | **Setuphelfer Identifier Migration:** Kontrollierte Ablösung aktiver `pi-installer`-Identifier mit Legacy-Ausnahmen |
| [deploy/DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP.md](deploy/DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP.md) | **Setuphelfer Identifier Cleanup:** Klassifizierung, sicherer Rewrite-Plan und kontrolliertes Apply mit Legacy-Backups |
| [deploy/DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE.md](deploy/DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE.md) | **Setuphelfer Identifier Cleanup Cycle:** Batch-Plan (max. 100), Apply und Postcheck ohne Evidence-Aenderung |
| [deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS.md](deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS.md) | **Legacy Identifier Hotspot Analysis:** Read-only Cluster/Kritikalitaet, priorisierte Cleanup-Ziele aus Inventory/Postcheck/Consistency |
| [deploy/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE.md](deploy/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE.md) | **Setuphelfer Identifier Hotspot Cleanup Cycle:** Cycle 2 aus Hotspot-Empfehlungen × Safe-Plan, max. 50 critical/high, Postcheck mit Inventory/Consistency/Hotspot |
| [deploy/DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION.md](deploy/DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION.md) | **Runtime Identifier Elimination:** Targets/Plan/Apply/Alias-Validation/Postcheck ohne Evidence-Doku-Schreibzugriffe; optional 1.7.1-Vorschlag nach Abschluss |
| [deploy/DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION.md](deploy/DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION.md) | **Runtime Identifier Zero State:** Verifikation Rest=0, optional Patch-Bump-Preparation/Apply/Postcheck ohne Release/Tag |
| [deploy/DEPLOY_SETUPHELFER_BRANDING_GUARD.md](deploy/DEPLOY_SETUPHELFER_BRANDING_GUARD.md) | **Setuphelfer Branding Guard:** Read-only Blocker gegen neue pi-installer-/PI_INSTALLER-Runtime-Treffer; Evidence-Handoff + optionales rg-Skript |
| [deploy/DEPLOY_LEGACY_RUNTIME_COMPATIBILITY.md](deploy/DEPLOY_LEGACY_RUNTIME_COMPATIBILITY.md) | **Legacy Runtime Compatibility:** Inventar/Koexistenz/Migrations-Empfehlungen/Upgrade-Matrix aus Handoff-JSON ohne echte Migration oder systemctl |
