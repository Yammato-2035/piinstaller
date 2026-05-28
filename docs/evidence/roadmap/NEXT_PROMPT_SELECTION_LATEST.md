# Next Prompt Selection (Latest)

**Selected:** `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF`

**Warum:** Liveness/Watchdog-MVP im Workspace; Runtime-Gate weiter Exit **14** (deploy_drift). Operator: Deploy-Helper/sync nach `/opt`; Restart nur bei Gate Exit **17/18** (Hang).

**Available next:** `BACKEND_RUNTIME_RECOVERY_GATE`, `BACKEND_WATCHDOG_IMPLEMENTATION_MVP`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Erst nach Operator-Handoff + belastbarem Runtime-Postcheck darf ein Rescue- oder Recovery-Folgeprompt empfohlen werden.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
