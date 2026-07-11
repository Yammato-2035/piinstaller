# PI-RS-MSI-FIX-001 — Console-Shield, boot-progress tty1 Race, MSI Safe-UI

Stand: 2026-07-12
Sprint-ID: **PI-RS-MSI-FIX-001**
Feature-Branch: `pi-rs-msi-fix-001-console-shield-boot-progress-tty1`

## Ausgangslage

| Feld | Wert |
|------|------|
| Payload vorher | **1.10.0.13** |
| Stick SHA256 (1.10.0.13) | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |
| Testgerät | MSI GE63 Raider RGB 8RF |
| SETUP_LOGS Session | `20260712_010101` |
| GRUB | MSI-Compat (`pci=noaer`, `setuphelfer_msi_compat=1`) |

### MSI-Compat Ergebnis (Session 3)

- PCIe-AER: **0 Zeilen** (Killer-E2500-Flut behoben)
- TUI: kurz sichtbar, dann **zerstört**
- GUI: `startx_not_started`, openvt VT2-Fehler, kein `Xorg.0.log`
- Backend/API: `/api/version` HTTP 200

## Root Cause

1. **`setuphelfer_rescue_shield_console_early`** fehlte in `setuphelfer-rescue-common.sh` → Journal: *Kommando nicht gefunden*
2. **`setuphelfer_rescue_should_auto_msi_evidence`** fehlte ebenfalls
3. **`boot-progress`** erzwang `show_tty … 1` mit `ESC[2J` + *„GUI übernimmt“*, während TUI/whiptail auf tty1 lief (Race ~01:00:28 vs 01:00:30)
4. Backend-/Journal-Ausgaben ohne Shield auf tty1 sichtbar → Textmenü überschrieben

Evidence: `docs/evidence/pi_rs_msi_fix_001_console_shield_boot_progress_tty1/msi-boot-20260712-session3-root-cause.txt`

## Fixes (Payload 1.10.0.14)

### Console-Shield (`setuphelfer_rescue_shield_console_early`)

- Dmesg-Konsole aus, systemd log-level warning
- Statusdatei `/run/setuphelfer/console-shield.json`
- Idempotent, boot-abbruchfrei
- Respektiert aktive TUI/Safe-UI (`tty1_clear_allowed=false`)

### boot-progress Race

- Kein erzwungenes `show_tty … 1` / `ESC[2J` bei TUI, whiptail, Safe-UI oder MSI-Compat
- Final-Status: *„Textmenü bereit“* statt *„GUI übernimmt“*
- Prüft `setuphelfer_rescue_tty1_clear_allowed`

### GUI/openvt Fallback

- openvt-Fehler klassifiziert: `startx_not_started` / `openvt_console_2_not_released`
- `tui_preserved=true`, `operator_next_action=use_tui_safe_mode`
- Kein tty1-clear bei GUI-Fail; `chvt 1` zurück zum TUI

### MSI Evidence Helper

- `setuphelfer_rescue_should_auto_msi_evidence` für Auto-Collect unter MSI-Compat

## Payload 1.10.0.14

| Feld | Wert |
|------|------|
| Artefakt | `build/rescue/filesystem.squashfs.repacked-1.10.0.14` |
| SHA256 | `665e44e40dfa5c384b85f4526d1a9dea6389a4ac60c9b1356e8530676a4c3ac7` |
| Repack-Script | `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh` |
| Quelle | `filesystem.squashfs.repacked-1.10.0.13` |

## Tests

- `backend/tests/test_pi_rs_msi_fix001_*.py` (Common, Shield, boot-progress, GUI-VT, Version)
- `scripts/check-rescue-payload-msi-fix001-content.sh` — content_ok
- `scripts/check-rescue-payload-no-secrets.sh` — passed

## Nicht durchgeführt

- **Kein USB-Schreiben** (siehe `docs/evidence/pi_rs_msi_fix_001_console_shield_boot_progress_tty1/no-usb-write.txt`)
- Kein physischer Boot-Smoke
- Kein produktiver Send, Backup, Restore, Wipe

## Nächster Schritt

**PI-RS-USB-MSI-FIX-001:** USB-Update auf Payload **1.10.0.14** + MSI-Boot-Retest am GE63 (MSI-Compat-Menü, TUI-Stabilität, optional GUI)
