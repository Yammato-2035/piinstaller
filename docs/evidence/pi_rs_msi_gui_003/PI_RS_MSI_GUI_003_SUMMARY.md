# PI-RS-MSI-GUI-003 — Kurzzusammenfassung

Stand: **2026-07-13**  
Status: **`passed`** (physischer Retest via PI-RS-MSI-AUTO-EVIDENCE-001)  
Payload: **1.10.0.20**

## Problem (physisch belegt, RETEST-002)

Auf MSI GE63 Raider RGB 8RF (`MS-16P5`) mit Payload **1.10.0.15** war die Whiptail-TUI trotz GUI-Sperre (PI-RS-MSI-GUI-002) **visuell zerstört**. Die Boot-Timeline zeigte um 11:12:22 noch `x11_starting` / „Grafische Oberfläche wird gestartet …“. Stale GUI-Logs aus Session `20260712_015909` wurden als aktuelle Evidence gelesen.

## Lösung

| Bereich | Maßnahme |
|---------|----------|
| Bootprofil | `boot_mode=tui_only` unter `setuphelfer_msi_compat=1` + nomodeset |
| Timeline | `tui_mode_selected` statt `x11_starting`; `gui_skipped` nur Audit |
| tty1 | Console-Ownership: nach TUI-Übergabe kein Boot-Progress-Write |
| Evidence | Session-ID pro Boot; Stale-Guard beim SETUP_LOGS-Mirror |
| Lab-Auto | PI-RS-MSI-AUTO-EVIDENCE-001 — unattended Retest 003/003B |

## Abschluss (2026-07-13)

Session **`20260713_003100_boot`**: TUI ≥120 s, kein `x11_starting`, Spät-Evidence maschinell, `lab-auto-result.json` **passed**.

## Verweise

- [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](../../rescue-stick/PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md)
- [PI_RS_MSI_GUI_003_FAQ.de.md](../../faq/PI_RS_MSI_GUI_003_FAQ.de.md)
