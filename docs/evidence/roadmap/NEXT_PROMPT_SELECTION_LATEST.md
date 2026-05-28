# Next Prompt Selection (Latest)

**Selected:** `BACKEND_RUNTIME_RECOVERY_GATE`

**Warum:** Operator-Output ist als Wahrheit ingestiert (Service aktiv, `/api/version` success, Runtime `/opt/setuphelfer/backend`), aber der Agent-Gate-Rerun aus Repo-CWD liefert `HTTP 000000`; daher zuerst konsolidierte Recovery-Gate-Klaerung.

**Available next:** `BACKEND_RUNTIME_OPERATOR_RESTART_RESULT_INGEST`, `BACKEND_RUNTIME_HANG_TRIAGE`, `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

**Regel:** Wenn Recovery-Gate danach Exit 0 ist, wird wieder `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE` empfohlen.

Siehe `NEXT_PROMPT_SELECTION_LATEST.json`.
