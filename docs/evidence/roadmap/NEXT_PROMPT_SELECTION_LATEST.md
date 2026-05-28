# Next Prompt Selection (Latest)

**Selected:** `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF`

**Warum:** Backend-Startup-Availability ist gehaertet, aber Runtime bleibt blockiert (Service aktiv + Port offen + HTTP-Timeout). Restart/Journals brauchen ein privilegiertes Operator-Terminal; im Agent-Kontext sind keine sudo/restart-Aktionen erlaubt.

**Available next:** `BACKEND_RUNTIME_RECOVERY_GATE`, `BACKEND_WATCHDOG_IMPLEMENTATION_MVP`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Erst nach Operator-Handoff + belastbarem Runtime-Postcheck darf ein Rescue- oder Recovery-Folgeprompt empfohlen werden.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
