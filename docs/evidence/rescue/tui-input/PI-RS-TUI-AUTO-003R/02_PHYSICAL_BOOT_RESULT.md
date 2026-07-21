# 02 – Physical Boot Result

Erfasst: `2026-07-21T21:05:07Z` (Dev-PC Import)

## Gerät
- DMI: Micro-Star / **GE63 Raider RGB 8RF** / Board **MS-16P5** / BIOS E16P5IMS.109
- Boot-ID: `2ecaddca-cea9-4295-9c42-21eb0fbbb3e6`
- Session: `rescue-session-20260721T230213Z-bb356a62`
- Payload: **1.10.0.60** (`all_versions_match=true`)

## GRUB / Kernelcmdline
Aus `boot_state_redacted.json` / dmesg:

```text
setuphelfer_mode=text
setuphelfer_tui_input_diag=1
setuphelfer_tui_input_diag_auto_shutdown=0
setuphelfer_msi_lab_auto=0
setuphelfer_auto_shutdown=0
```

Diagnose-GRUB-Eintrag: **ja** (cmdline belegt).

## Diagnose-Pfad
| Check | Ergebnis |
|-------|----------|
| Diagnose-GRUB gewählt | **ja** |
| tty1 TUI (`setuphelfer-rescue-tui`) | **ja** (ps Snapshot) |
| tty2 Diagnose (`python3 -m core.rescue_tui_input_diagnostic`) | **ja** (PID 1857 im Snapshot) |
| Sessiondauer bis `shutdown_pending` | ~24 s (`23:02:13Z` → `23:02:37Z`) |
| RUN_ID sichtbar / notiert | **nein** (Operator) |
| `SETUP_LOGS/tui-input-diagnostics/` | **fehlt** |
| `.partial`-Reste | **keine** |
| Persistenz finalisiert | **nein** |

## Operator-Aussage (nicht maschinell gemessen)
- Tastenfunktion: **funktioniert** („das Drücken der Tasten funktioniert“)
- Manueller Tasten-Choreografie-Test: vom Operator als unbrauchbar abgelehnt

## Nebenbeobachtungen (Journal)
- `setuphelfer_rescue_kill_gui_leftovers: Kommando nicht gefunden` in `setuphelfer-rescue-tui` (Zeile 646/548) — nicht die Persistenzfrage, aber Noise auf dem Lauf.
