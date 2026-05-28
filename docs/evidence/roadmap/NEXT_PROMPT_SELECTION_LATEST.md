# Next Prompt Selection (Latest)

**Selected:** `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Warum:** Operator-Terminal Ground Truth: `./scripts/check-runtime-deploy-gate.sh` → OK (Exit 0). Read-only Agent-Verify: health/version 200, deploy_drift green, `safe_test_mode` UNLOCKED, `core/liveness.py` in `/opt`. Kein Rescue in diesem Ingest-Lauf.

**Available next:** `BACKEND_RUNTIME_RECOVERY_GATE`, `BACKEND_WATCHDOG_IMPLEMENTATION_MVP`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Erst nach Operator-Handoff + belastbarem Runtime-Postcheck darf ein Rescue- oder Recovery-Folgeprompt empfohlen werden.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
