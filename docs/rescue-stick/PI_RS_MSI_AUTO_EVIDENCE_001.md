# PI-RS-MSI-AUTO-EVIDENCE-001 — Unattended MSI Lab Boot

**Stand:** 2026-07-13  
**Payload:** **1.10.0.20**  
**Status:** **passed** (GE63 Raider, Session `20260713_003100_boot`)

## Ziel

Physischer MSI-Laptop bootet vom Stick **ohne Operator-Eingriff**, sammelt Spät-Evidence + RS-011B, bewertet das Ergebnis und fährt herunter.

## Architektur

```text
GRUB (default=0, timeout=3, MSI-Lab-Cmdline)
  → Live-Boot (msi_compat, lab_auto, auto_shutdown, late_sec=120)
  → setuphelfer-rescue-auto-msi-evidence.service
       → Backend ready
       → Late gate (uptime ≥ 150 s)
       → late-evidence-*.txt + RS-011B collect
       → lab-auto-result.json (Python eval)
       → poweroff (evidence_complete)
  → setuphelfer-rescue-lab-auto-shutdown-failsafe.timer (420 s, nur Fallback)
```

## Kernel-Cmdline (GRUB-Lab-Modus)

- `setuphelfer_msi_compat=1`
- `setuphelfer_msi_lab_auto=1`
- `setuphelfer_auto_shutdown=1`
- `setuphelfer_msi_lab_late_sec=120`
- `nomodeset`, `nouveau.modeset=0`, `pci=noaer`

## Kernkomponenten

| Komponente | Pfad |
|------------|------|
| GRUB-Patch | `backend/core/rescue_msi_lab_auto_boot.py` |
| GRUB-Skript | `scripts/rescue/configure-stick-msi-lab-auto-grub.sh` |
| Auto-Evidence | `scripts/rescue-live/image/setuphelfer-rescue-auto-msi-evidence` |
| Failsafe | `setuphelfer-rescue-lab-auto-shutdown-failsafe` + `.timer` |
| Eval | `backend/core/rescue_msi_lab_evidence_eval.py` |
| Import | `scripts/rescue/import-msi-rs011b-evidence.sh` |
| CSE Preview | `setuphelfer_cse/rescue_boot_evidence/preview.py` |

## Repack-Hinweis (Failsafe)

Der Failsafe-**Service** darf **nicht** in `multi-user.target.wants` verlinkt sein — nur der **Timer** (`OnBootSec=420s`). Siehe `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh`.

## Erfolgskriterien

Siehe `lab-auto-result.json`:

- `capture_after_120s`: true
- `tui_owned`: true (Spät-Capture)
- `manual_late_evidence_file_present`: true
- `result_status`: `passed`
- `boot_state` Phase: `auto_shutdown_evidence_complete`

## Abnahme

| Auftrag | Status |
|---------|--------|
| PI-RS-MSI-AUTO-EVIDENCE-001 | **passed** |
| PI-RS-MSI-RETEST-003 | **passed** (superseded) |
| PI-RS-MSI-RETEST-003B | **passed** (superseded) |

Evidence: `docs/evidence/pi_rs_msi_auto_evidence_001/`

## Siehe auch

- [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md)
- [PI_RS_MSI_AUTO_EVIDENCE_001_OPERATOR_RUNBOOK.md](../test-plans/PI_RS_MSI_AUTO_EVIDENCE_001_OPERATOR_RUNBOOK.md)
