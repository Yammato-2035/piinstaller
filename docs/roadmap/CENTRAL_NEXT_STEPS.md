# Central Next Steps

Stand: 2026-07-13 (PI-RS-MSI-AUTO-EVIDENCE-001 **passed**, Payload **1.10.0.20**)

## Empfohlene Reihenfolge

1. Optional: **PI-RS-TEL-LIVE-001** — Telemetry-Send vom gebooteten Stick (nur mit expliziter Freigabe)
2. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot
3. Optional: `tui_mode_selected` in Boot-Timeline für Lab-Auto nachziehen (nicht blockierend)

## Abgeschlossen (Referenz)

- **PI-RS-MSI-AUTO-EVIDENCE-001** — unattended MSI lab boot **passed** (GE63, Session `20260713_003100_boot`)
- **PI-RS-MSI-RETEST-003 / 003B** — **passed** (superseded by auto-lab)
- **PI-RS-MSI-GUI-003** — TUI/Console-Isolation **passed** on hardware
- PI-RS-USB-UPDATER-001 — atomarer Payload-Write
- PI-RS-MSI-GUI-002 — GUI unter MSI-Compat gesperrt
- PI-RS-MSI-FIX-001 — Console-Shield 1.10.0.14
- PI-RS-TEL-SEND-001 — Lab Send accepted

## Offen

- TEL-CLOUD-HEALTH-001 / TEL-CLOUD-FIX-001 — IONOS TLS/Proxy
- Telemetry production send (gated)
