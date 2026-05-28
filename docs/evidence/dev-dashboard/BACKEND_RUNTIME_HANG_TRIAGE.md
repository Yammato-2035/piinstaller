# Backend Runtime Hang Triage

- Datum/Zeit (UTC): 2026-05-28T03:44:00Z
- Modus: STRICT MODE, read-only Triage
- Service: `setuphelfer-backend.service`

## Ergebnisstand

- Die urspruengliche Hang-Triage (Service aktiv, API-Timeouts) wurde unveraendert archiviert.
- Nachfolgender Operator-Restart-Output wurde separat ingestiert und gilt als aktuellere Wahrheit.
- Siehe dazu: `BACKEND_RUNTIME_RESTART_RESULT.md` und `backend_runtime_restart_result_latest.json`.

## Urspruengliche Klassifikation

- Primaere Klasse: `backend_runtime_hang_accept_queue_saturation`
- Sekundaer: `backend_api_hang_suspected`, `runtime_service_active_but_http_unresponsive`

## Status dieses Artefakts

- Dieses Artefakt bleibt als Vorbefund bestehen (`historical_pre_recovery_triage`).
- Folgeschritte laufen ueber Recovery-Gate und Ingest-Delta.
