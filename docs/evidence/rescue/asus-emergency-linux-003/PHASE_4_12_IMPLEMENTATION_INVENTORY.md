# PHASE_4_12_IMPLEMENTATION_INVENTORY

Stand: 2026-08-06  
Workspace: `/home/volker/piinstaller-asus-emergency-linux-telemetry-003`  
Vergleich: `83126971..2deb694b` (63 Dateien)

Maschinenlesbar: `phase_4_12_implementation_inventory.json`

## Tabelle

| Komponente | Datei | im Payload erforderlich | im initramfs erforderlich | im Bootloader erforderlich | getestet |
|---|---|---:|---:|---:|---:|
| Boot-Stage-Sentinel | `backend/rescue/boot_stage_sentinel.py` | ja | nein* | nein | ja (unit) |
| Hardware-State-Sentinel | `backend/rescue/hardware_state_sentinel.py` | ja | nein | nein | ja (unit) |
| Kernel-Event-Sentinel | `backend/rescue/kernel_event_sentinel.py` | ja | nein | nein | ja (unit) |
| Device-Lifecycle-Sentinel | `backend/rescue/device_lifecycle_sentinel.py` | ja | nein | nein | ja (unit) |
| Driver-Failure-Resolver | `backend/rescue/driver_failure_resolver.py` | ja | nein | nein | ja (unit) |
| Boot-Comparison-Engine | `backend/rescue/boot_comparison_engine.py` | ja | nein | nein | ja (unit) |
| ASUS-Bootprofile (Logik) | `backend/rescue/asus_boot_profiles.py` | ja | nein | **ja** (Cmdline/Menü) | ja (unit) |
| Telemetrie-Spooler | `backend/rescue/telemetry_spooler.py` | ja | nein | nein | ja (unit) |
| Diagnostikcontract | `backend/rescue/diagnostics_forwarding_contract.py` | ja | nein | nein | ja (unit) |
| Dashboard-View | `backend/rescue/operator_dashboard_boot_view.py` | ja (Host/UI) | nein | nein | smoke |
| systemd boot-sentinel | `scripts/rescue-live/image/systemd/setuphelfer-boot-sentinel.service` | ja | nein | nein | nein (im Image) |
| systemd hardware-sentinel | `…/setuphelfer-hardware-sentinel.service` | ja | nein | nein | nein (im Image) |
| systemd kernel-event | `…/setuphelfer-kernel-event-sentinel.service` | ja | nein | nein | nein (im Image) |
| systemd telemetry-spooler | `…/setuphelfer-telemetry-spooler.service` | ja | nein | nein | nein (im Image) |
| systemd autocapture | `…/setuphelfer-autocapture-finalizer.service` | ja | nein | nein | nein (im Image) |
| Sentinel-Tests | `backend/tests/test_asus_boot_sentinels_v1.py` | nein | nein | nein | ja |
| Evidence/Matrix | `docs/evidence/rescue/asus-emergency-linux-003/*` | nein | nein | nein | n/a |
| API-Routen ASUS-neu | — | **fehlt** | nein | nein | nein |
| i18n DE/EN/FR/NL neu | — | **fehlt** (Baseline-i18n vorhanden) | nein | nein | nein |
| GRUB-Menüeinträge ASUS-00..05 | noch nicht in live-build-Tree verdrahtet | ja | nein | **ja** | nein |

\* Early markers vor Userspace bleiben unvollständig ohne Bootloader-/initramfs-Hooks; Userspace-Sentinels ab `systemd_started` reichen für ASUS-00 Forensic TUI.

## Buildpfad-Implikation

Weil **Bootloader-Profile** und **systemd-Units** neu sind und **kein Basis-ISO/SquashFS** im Worktree liegt → **Controlled ISO Build required** (siehe `ASUS_CARRIER_BUILD_PATH_DECISION.md`).
