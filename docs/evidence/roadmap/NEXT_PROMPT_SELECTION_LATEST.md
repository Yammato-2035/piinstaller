# Next Prompt Selection (Latest)

**Selected:** `BACKEND_RUNTIME_HANG_TRIAGE`

**Warum:** Autorisierter Restart war im Agent-Kontext nicht ausführbar (sudo braucht TTY/Passwort). Backend bleibt aktiv/listening, API bleibt timeout.

**Available next:** `BACKEND_RUNTIME_RECOVERY_GATE`

**Nicht:** weiterer Restart im Agent ohne passenden Operator-Terminal-Kontext; kein Rescue-/Backup-/Restore-Run.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
