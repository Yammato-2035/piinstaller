# Rescue Orchestrator Preview – KB

## Warum erst Preview?

Preview reduziert Risiko: Zielprüfung + Verify + Dryrun, bevor irgendeine echte Wiederherstellung möglich wäre.

## Warum kein Restore in Phase 1?

Diese Phase validiert nur Entscheidungsgrundlagen. Ein Execute-Schritt ist absichtlich nicht enthalten.

## Warum blockiert Safety mein Ziel?

System-/Live-/Windows-/Dualboot-/Unknown-Ziele bleiben hart blockiert. Der Orchestrator respektiert diese Gates unverändert.

## Warum wird Preflight empfohlen?

Fehlt ein nachweisbarer Preflight-Plan, wird nicht zwingend blockiert, aber als Risiko markiert (`RESCUE_PREFLIGHT_RECOMMENDED`).
