# Next Prompt Selection (Latest)

**Selected:** `DEPLOY_DRIFT_TRIAGE_AFTER_WATCHDOG`

**Warum:** Deploy-Sync mit Freigabe versucht; `sudo systemctl start setuphelfer-deploy-helper.service` im Agent blockiert (`deploy_helper_blocked_by_sudo_tty`). Gate bleibt Exit **14**. Operator startet Deploy-Helper im privilegierten Terminal; bei Gate 0 → `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`.

**Available next:** `BACKEND_RUNTIME_RECOVERY_GATE`, `BACKEND_WATCHDOG_IMPLEMENTATION_MVP`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Erst nach Operator-Handoff + belastbarem Runtime-Postcheck darf ein Rescue- oder Recovery-Folgeprompt empfohlen werden.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
