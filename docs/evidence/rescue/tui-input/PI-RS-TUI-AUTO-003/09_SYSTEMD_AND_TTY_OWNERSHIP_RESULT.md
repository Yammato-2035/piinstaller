# 09 – Systemd and TTY Ownership Result

Incidental ownership (GUI-Boot → TUI):

- `owner=tui`, `lifecycle_state=tui_owned`
- `gui_transition_allowed=false` zum Capture-Zeitpunkt

Keine Erfassung konkurrierender tty1-FDs durch den Diagnosemodus.

TTY-Konkurrenz (AUTO-003): **none** (nicht prüfbar) → incidental: **possible** Übergang GUI→TUI, aber nicht die geforderte Diagnose.
