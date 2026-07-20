# 02 – Physical Boot Result (Retry)

## Gerät / Payload

- MSI GE63 Raider RGB 8RF / MS-16P5
- Payload **1.10.0.59**
- Session `20260720_222258_boot` / diagnostics `20260720_222240_boot`

## GRUB / Cmdline

**Diagnoseeintrag gestartet:** ja

```text
setuphelfer_mode=text
setuphelfer_tui_input_diag=1
setuphelfer_tui_input_diag_auto_shutdown=0
```

## Runtime (incidental diagnostics pack)

| Beobachtung | Beleg |
|-------------|-------|
| Diagnoseprozess auf tty2 | `python3 -m core.rescue_tui_input_diagnostic` PID 1778 (`60-ps.txt`, Ss+) |
| Normale TUI auf tty1 | `whiptail … Textmodus` PID 2537 (late-evidence 22:25) |
| Evidence-Root `tui-input-diagnostics/` | **fehlt** auf SETUP_LOGS |
| Finalisierte Run-Dateien 00–20 | **fehlen** |

## Bewertung

```text
diagnostic_grub_entry_selected=true
diagnostic_tty_reached=true   # Prozess auf tty2
run_completed=false
evidence_complete=false
abort_or_incomplete=evidence_not_finalized
```

Vermutlich: Assistent nicht bis Finalize durchlaufen (kein Input / vorzeitiges Herunterfahren) — `/run`-Evidence geht beim Reboot verloren.
