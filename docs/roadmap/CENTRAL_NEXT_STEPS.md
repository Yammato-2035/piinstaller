# Central Next Steps

Stand: 2026-07-12 (PI-RS-MSI-FIX-001 Payload 1.10.0.14)

## Empfohlene Reihenfolge

1. **PI-RS-USB-MSI-FIX-001** — Stick auf Payload **1.10.0.14** aktualisieren + GE63 MSI-Boot-Retest (`docs/rescue-stick/PI_RS_MSI_FIX_001_CONSOLE_SHIELD_BOOT_PROGRESS_TTY1.md`)
2. SETUP_LOGS importieren → TUI-Stabilität + optional Telemetry Preview
3. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot

## Abgeschlossen (Referenz)

- PI-RS-MSI-FIX-001 — SquashFS **1.10.0.14** repacked (Console-Shield, boot-progress Race, GUI-Fallback)
- PI-RS-MSI-RETEST-002 Session 3 — Root Cause dokumentiert (fehlende Helper, tty1 Race)
- PI-RS-USB-TELEMETRY-001 — USB Payload-Update auf **1.10.0.13** (verify OK)
- PI-RS-PAYLOAD-TELEMETRY-001 — SquashFS Repack
- PI-RS-TEL-SEND-001 — Lab Send accepted (`req-fd36496e-…`)

## Offen

- USB-Update auf **1.10.0.14** + MSI-Boot-Smoke (Token nicht im Payload)
