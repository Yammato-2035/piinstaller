# MSI TUI & Console Isolation (PI-RS-MSI-GUI-003)

**As of:** 2026-07-13  
**Payload:** 1.10.0.20  
**Status:** **passed** (physical retest complete)

## Context

| Sprint | Outcome |
|--------|---------|
| PI-RS-MSI-FIX-001 | Console shield, fewer tty1 clears |
| PI-RS-MSI-GUI-002 | GUI blocked under MSI compat |
| PI-RS-MSI-RETEST-002 | **failed** — TUI corrupted, `x11_starting` in timeline |
| **PI-RS-MSI-GUI-003** | Boot progress + tty1 isolation + session evidence |

**Test hardware:** MSI GE63 Raider RGB 8RF, model MS-16P5.

## Root cause (confirmed / strongly supported)

1. **Boot progress** used a fixed phase list including `x11_starting`, ignoring `gui-availability.json`.
2. **tty1 conflict:** boot-progress service and Whiptail TUI run in parallel on `/dev/tty1`.
3. **Console shield v1** had `tty1_clear_allowed` but no explicit **`tty1_write_allowed`** after TUI handoff.
4. **Stale evidence:** GUI logs without session binding — old session `20260712_015909` mixed into new boot.
5. **Version drift:** repack did not sync `config/version.json` → `/api/version` reported 1.10.0.12 while ESP showed 1.10.0.15.

## Architecture (1.10.0.16)

Central profile → timeline plan → session init → console ownership → stale-safe mirror.

Key modules: `rescue_msi_boot_profile.py`, `rescue_boot_timeline.py`, `rescue_console_ownership.py`, `rescue_session_evidence.py`, `rescue_payload_version_carriers.py`.

## Operator notes

- Physical retest **passed** via **PI-RS-MSI-AUTO-EVIDENCE-001** (session `20260713_003100_boot`, payload **1.10.0.20**)
- Summary: [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)

## References

- [PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md](../../faq/PI_RS_MSI_AUTO_EVIDENCE_001_FAQ.en.md)
- [MSI_LAB_AUTO_EVIDENCE_KB_EN.md](MSI_LAB_AUTO_EVIDENCE_KB_EN.md)

- [PI_RS_MSI_GUI_003_FAQ.en.md](../../faq/PI_RS_MSI_GUI_003_FAQ.en.md)
- [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](../../rescue-stick/PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md)
- Evidence: `docs/evidence/pi_rs_msi_gui_003/`
