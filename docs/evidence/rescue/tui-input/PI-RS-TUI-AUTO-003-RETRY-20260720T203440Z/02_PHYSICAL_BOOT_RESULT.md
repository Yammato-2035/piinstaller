# 02 – Physical Boot Result

| Feld | Wert |
|------|------|
| Gerät | MSI GE63 / MS-16P5 |
| Payload | 1.10.0.59 |
| Session/Boot | `c671ea34-…` / diagnostics `20260720_223217_boot` |
| Diagnose-GRUB | **ja** (`setuphelfer_tui_input_diag=1`) |
| tty2-Prozess | **ja** `python3 -m core.rescue_tui_input_diagnostic` PID 1762 Ss+ |
| `SETUP_LOGS/tui-input-diagnostics/` | **fehlt** |
| Import | blocked |

## Evidence-Pfad-Analyse (Code + Stick)

`resolve_evidence_root()` ruft `resolve_setup_logs(allow_mount=False)` auf. Schlägt das fehl, fällt es auf:

```text
/run/setuphelfer/tui-input-diagnostics
```

zurück (tmpfs → **Verlust beim Herunterfahren**).

Setup-Logs-Resolver (Discovery) meldete später:

```text
actual_mountpoint=/run/setuphelfer/esp-rw
writable=true
resolved_at=2026-07-20T22:32:21Z
```

Diagnoseprozess war bereits um ~22:32 aktiv → **Race**: Evidence sehr wahrscheinlich unter `/run`, nicht auf dem Stick persistiert.

```text
diagnostic_grub_entry_selected=true
diagnostic_tty_reached=true
run_completed=false
evidence_complete=false
likely_cause=evidence_root_run_fallback_lost_on_reboot
```
