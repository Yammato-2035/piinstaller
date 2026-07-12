# PI-RS-MSI-GUI-003 — Code Path Map

| Funktion | Datei | Auslöser | schreibt tty1 | MSI-Compat berücksichtigt | Risiko |
| -------- | ----- | -------- | ------------: | ------------------------: | ------ |
| `x11_starting` Phase | `setuphelfer-rescue-boot-progress` | systemd oneshot | optional (`show_tty`) | teilweise (`SAFE_TTY`) | **hoch** → GUI003: Python-Plan |
| Boot-Phasenplanung | `backend/core/rescue_boot_timeline.py` | boot-progress `_load_plan` | nein | **ja** (`tui_mode_selected`) | niedrig |
| Zentrales Bootprofil | `backend/core/rescue_msi_boot_profile.py` | cmdline | nein | **ja** | niedrig |
| Console-Shield v1 | `setuphelfer-rescue-common.sh` | `shield_console_early` | indirekt | teilweise | mittel → v2 Ownership |
| tty1 Ownership | `backend/core/rescue_console_ownership.py` | TUI/Boot-Transition | nein | **ja** | niedrig |
| Whiptail TUI | `setuphelfer-rescue-tui.sh` | entrypoint | **ja** | GUI-Menü gesperrt | mittel |
| GUI-Verfügbarkeit | `setuphelfer-rescue-common.sh` | MSI-Compat-Check | nein | **ja** | niedrig |
| GUI-Fallback | `setuphelfer-rescue-common.sh` | Watchdog/TUI | nein | **ja** | niedrig |
| GUI-Start | `setuphelfer-rescue-gui-watchdog.sh` | kiosk/gui mode | VT/X11 | **ja** (blocked) | niedrig |
| Session-ID | `backend/core/rescue_session_evidence.py` | boot-progress/TUI init | nein | **ja** | niedrig |
| SETUP_LOGS Harvest | `setuphelfer-rescue-common.sh` `mirror_evidence_file` | runtime writes | nein | Stale-Guard GUI003 | mittel |
| Runtime-Logs | `/run/setuphelfer/*.log` | GUI chain | nein | Session-Reinit | mittel |
| Versionsträger | `repack-rescue-squashfs-react-shell.sh` | repack | nein | Sync `version.json` | niedrig |
