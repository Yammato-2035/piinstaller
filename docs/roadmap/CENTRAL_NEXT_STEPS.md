# Central Next Steps

Stand: 2026-07-12 (PI-RS-USB-MSI-FIX-001 Payload 1.10.0.14)

## Empfohlene Reihenfolge

1. **PI-RS-USB-MSI-FIX-001 Operator Boot** — GE63 mit Stick **1.10.0.14** + **MSI-Compat** GRUB booten (`docs/rescue-stick/PI_RS_USB_MSI_FIX_001_USB_UPDATE_1_10_0_14_BOOT_RETEST.md`)
2. SETUP_LOGS importieren → TUI-Stabilität + Console-Shield prüfen
3. Optional: Telemetry Preview vom gebooteten Stick (kein Send ohne Token)
4. **CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot

## Abgeschlossen (Referenz)

- PI-RS-USB-MSI-FIX-001 — USB Payload **1.10.0.13 → 1.10.0.14**, verify OK
- PI-RS-MSI-FIX-001 — SquashFS 1.10.0.14 (Console-Shield, boot-progress Race, GUI-Fallback)
- PI-RS-MSI-RETEST-002 Session 3 — Root Cause dokumentiert
- PI-RS-TEL-SEND-001 — Lab Send accepted (`req-fd36496e-…`)

## Offen

- GE63 MSI-Compat Boot-Retest mit **1.10.0.14**
- SETUP_LOGS Import nach Boot
- `version.json` auf FAT32: `project_version` noch 1.10.0.13 (Metadaten-Drift, SquashFS-SHA maßgeblich)
