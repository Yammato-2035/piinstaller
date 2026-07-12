# Central Next Steps

Stand: 2026-07-12 (PI-RS-MSI-GUI-002 Payload 1.10.0.15)

## Empfohlene Reihenfolge

1. **PI-RS-USB-MSI-GUI-002** — USB-Update auf Payload **1.10.0.15** + GE63 MSI-Compat Boot-Retest (`docs/rescue-stick/PI_RS_MSI_GUI_002_DISABLE_GUI_UNDER_MSI_COMPAT.md`)
2. SETUP_LOGS importieren → TUI stabil, GUI-Menü gesperrt, keine openvt/chvt-Zerstörung
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
