# Rettungsstick – Read-only Build-Gate IST-Analyse

**Datum:** 2026-05-24  
**HEAD:** `ffd2d8a`  
**Modus:** Analyse nur – **kein** ISO-Build, **kein** chroot, **kein** apt.

## 1. Vorhandene Rescue-Komponenten

| Bereich | Pfade / Artefakte | Ampel |
|---------|-------------------|--------|
| API Rescue | `backend/api/routes/rescue.py`, `backend/rescue/routes.py` | **green** |
| Core Safety | `backend/core/rescue_allowlist.py`, `rescue_hardstop.py` | **green** |
| Module | `backend/modules/rescue_*.py` (discovery, dryrun, gate, target_assessment, …) | **green** |
| Orchestrator | `backend/rescue/orchestrator.py`, `restore_preview_orchestrator.py` | **green** |
| Deploy Runner (40+) | `backend/deploy/runner_rescue_*.py` | **green** |
| Partitions-Handoff | `docs/architecture/RESCUE_STICK_PARTITION_HANDOFF.md` | **green** |
| Skripte (Template) | `scripts/rescue/build-rescue-iso.sh`, `build-rescue-iso-controlled.sh` | **review_required** (Template, kein Standard-Build) |
| KB Recovery | `docs/knowledge-base/recovery/*.md` (22 Dateien) | **green** |

## 2. Build-/Sandbox-/Emulation-Komponenten

| Komponente | Beschreibung | Ampel |
|------------|--------------|--------|
| `runner_rescue_build_sandbox_preparation.py` | Sandbox-Vorbereitung unter `build/rescue/` | **green** |
| `runner_rescue_build_environment_emulation.py` | Emulation-Snapshot, simulated workspace/outputs | **green** |
| `runner_rescue_sandbox_controlled_copy.py` | Kontrollierte Kopie in Sandbox | **green** |
| `runner_rescue_dry_build_orchestration.py` | Dry-Build-Orchestrierung | **green** |
| `runner_rescue_build_readiness_gate.py` | Aggregiert Handoff-JSONs vor Build | **green** |
| `runner_rescue_debian_live_build_plan.py` | Debian-Live-Plan (Handoff) | **green** |
| `runner_rescue_debian_live_build_inputs.py` | Build-Inputs (read-only Spec) | **green** |
| `runner_rescue_iso_*` | Readiness, execution **plan**, artifact prep (kein Live-Build in diesem Lauf) | **review_required** |
| `runner_rescue_live_build_config_generator.py` | Live-Config-Generator | **green** |
| `build/rescue/emulation/` | Emulierte Artefakte (Workspace) | **review_required** (falls Handoffs fehlen: blocked) |

## 3. Handoff-Dateien

Typische Pfade unter `docs/evidence/runtime-results/handoff/`:

- `rescue_live_os_base_decision.json`
- `rescue_stick_component_inventory.json`
- `rescue_mvp_scope_gate.json`
- `rescue_debian_live_build_plan.json`
- `rescue_build_readiness_gate.json`
- `rescue_build_emulation_final_gate.json`
- Partitions: `RESCUE_STICK_PARTITION_HANDOFF_READONLY.md`

**Ampel:** **review_required** – Runner vorhanden; Vollständigkeit pro Gate-Lauf zu prüfen.

## 4. Vorhandene Tests

| Muster | Anzahl (ca.) |
|--------|----------------|
| `backend/tests/test_deploy_runner_rescue_*_v1.py` | 35+ Module |
| Partitions Finalisierung | `test_partitions_*_v2.py`, Storage-Facade v1 |

**Ampel:** **green** (Unit/Handoff-Tests für Runner)

## 5. Fehlende Bausteine vor echtem ISO-Build

| Baustein | Ampel | Anmerkung |
|----------|--------|-----------|
| Debian-Live-Konfiguration final | **review_required** | Plan/Inputs-Runner vorhanden, kein `lb build` |
| Paketliste produktionsreif | **review_required** | In Handoffs/Plan referenziert, nicht final verifiziert |
| Runtime-Bundle im Stick | **review_required** | `runner_rescue_runtime_bundle_manifest.py`, Seal unter `build/rescue/` |
| Frontend-Bundle im Live-OS | **review_required** | Assembly-Pipeline-Runner, kein Live-Deploy |
| Backend-Start im Live-System | **review_required** | systemd-Preview in Packaging, Live-Test fehlt |
| Netzwerk/Web-UI-Start Live | **blocked** | Kein erfolgreicher Live-Boot-Nachweis |
| Read-only Root-Konzept | **review_required** | `runner_rescue_readonly_mount_orchestrator.py`, Policy-Doku |
| Overlay/Persistence-Konzept | **review_required** | `overlay_workspace_plan.json`, Emulation |
| Bootloader/EFI-Konzept | **review_required** | `runner_rescue_efi_boot_analyzer.py`, kein Hardware-EFI-Test |
| Hardware-Testplan | **review_required** | `runner_rescue_live_hardware_matrix.py`, VM-Test-Orchestrator |
| Partitions-Final read-only | **green** | `ffd2d8a`, Browser-Smoke dokumentiert |
| Echter ISO-Build | **blocked** | Bewusst nicht freigegeben |

## 6. Gesamt-Ampel (Build-Gate)

| Kategorie | Status |
|-----------|--------|
| Vorbereitung / Runner / Doku | **review_required** |
| Echter ISO-/Live-Build | **blocked** |
| Partitions-Handoff an Rescue | **green** |

**Nächster erlaubter Schritt:** Read-only Build **Emulation** (Workspace-Snapshot, Paketlisten-Preview) gemäß `docs/prompts/PROMPT_RESCUE_STICK_READONLY_BUILD_EMULATION.md` – ohne `lb build`, chroot, apt, mount, dd, xorriso, qemu.
