# PI-RS-BVR-GUI-VT-PROGRESS-002 – Baseline

## Freeze

- **BVR-Core:** eingefroren (`bvr_core_frozen: true`). Backup-/Verify-/Restore-/Manifest-Algorithmen unverändert.
- **Baseline-Commit:** `92bfcc15`
- **Run-ID:** `e2e-rescue-msi-20260722-002744-a8f0a50d`
- **Payload:** `1.10.1.1`

## Ergebnis Baseline-Lauf

| Feld | Wert |
|------|------|
| BVR | passed (166 Dateien, ~130 MB) |
| HTTP | ready (`/health.json` 200) |
| Chromium laut ui-status | gestartet (`auto-e2e-progress.html`) |
| GUI für Operator | **nicht sichtbar** |
| Fallback-Code (Evidence) | `openvt_console_2_not_released` (**stale** gui-watchdog.json vom 2026-07-17) |
| gui-fallback.json | `msi_compat_nomodeset` / `openvt_attempted:false` (**widerspricht** gui-start.log) |
| TUI/auto-e2e-state | `sabrent_waiting` / phase_index=4 |
| physical-progress | `shutdown` / erfolgreich |
| Gesamt | `passed_with_gui_fallback` |

## Erlaubte Änderungsflächen

VT-Auswahl, X11-/Chromium-Launcher, GUI-Lifecycle, Watchdog-Handoff, Fortschrittsmodell, TUI-/GUI-/DCC-Statusleser, i18n, Dokumentation.
