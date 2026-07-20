# 02 – Physical Boot Result

## Gerät

- DMI: Micro-Star / **GE63 Raider RGB 8RF** / Board **MS-16P5**
- Session: `20260720_221125_boot` / diagnostics `20260720_221100_boot`
- Payload laut Collector: **1.10.0.59**

## GRUB / Kernelcmdline (Stick-Evidence)

```text
setuphelfer_mode=gui
setuphelfer_kiosk=1
setuphelfer_gui_watchdog=1
setuphelfer_msi_lab_auto=0
setuphelfer_auto_discovery=0
# KEIN setuphelfer_tui_input_diag=1
```

Das entspricht dem **Standard-Eintrag** „Lab-Auto (GUI, Backup/Verify)“ (`set default=0`), **nicht** dem Diagnoseeintrag.

## Diagnose-Pfad

| Check | Ergebnis |
|-------|----------|
| Diagnose-GRUB gewählt | **nein** (cmdline belegt) |
| tty2-Diagnose gestartet | **nein** |
| `SETUP_LOGS/tui-input-diagnostics/` | **fehlt** |
| Assistenten-Evidence (00–20, SHA256SUMS) | **fehlt** |

## Laufstatus

```text
diagnostic_grub_entry_not_selected
diagnostic_ui_not_reached
run_completed=false
```

Nebenbefund: GUI/Chromium startete kurz; Console-Owner wurde `tui`; `whiptail` Textmenü auf tty1 sichtbar (wie bekannter Hang-Pfad) — **kein** Ersatz für AUTO-003-Diagnose.
