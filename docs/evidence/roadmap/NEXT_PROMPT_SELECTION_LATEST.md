# Next Prompt Selection (Latest)

**Selected:** `RESCUE_ISO_CHROOT_MOUNT_CLEANUP_TROUBLESHOOT`

**Warum:** Chroot-Cleanup-Fehler (`RESCUE-BUILD-CHROOT-CLEANUP-001`) analysiert; Runtime-Gate grün. Operator muss Mount-Cleanup unter BUILD_TREE per Handoff ausführen — kein Agent-sudo, kein Build-Retry in diesem Lauf.

**Nach erfolgreichem Cleanup + Retry:** `RESCUE_ISO_ARTIFACT_VERIFY` oder `RESCUE_ISO_BUILD_FAILURE_TRIAGE`.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
