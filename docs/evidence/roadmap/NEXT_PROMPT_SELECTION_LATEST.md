# Next Prompt Selection (Latest)

**Selected:** `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF`

**Warum:** Aktueller Audit zeigt haengenden Backend-Zustand (Service aktiv + Port 8000 listening, aber API-Endpunkte timeouten). Restart/Journals brauchen ein privilegiertes Operator-Terminal; im Agent-Kontext sind keine sudo/restart-Aktionen erlaubt.

**Available next:** `BACKEND_RUNTIME_HANG_TRIAGE`, `BACKEND_RUNTIME_RECOVERY_GATE`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Erst nach Operator-Handoff + belastbarem Runtime-Postcheck darf ein Rescue- oder Recovery-Folgeprompt empfohlen werden.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
