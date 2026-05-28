# BACKEND_STARTUP_FAILURE_MODEL

## Klassifikationen

- `backend_ok`: Service + Port + `/health` + `/api/version` OK
- `backend_down`: Service down oder Port nicht offen
- `backend_hanging`: Service aktiv + Port offen + HTTP Timeout
- `backend_degraded`: `/health` ok, aber `/api/version` oder Dashboard-API fehlerhaft
- `backend_unknown`: kein eindeutiges Signal

## Verbindliche Aussagen

- `backend_hanging` ist ein harter Fehler.
- Port offen reicht nicht.
- `systemd active` reicht nicht.
- `/health` bleibt leichtgewichtig.
- `/api/version` bleibt schnell und robust.

## Runtime-Gate Mapping

- `backend_hanging_active_port_but_http_timeout` → Exit `17`
- API-Fehler ohne Hang-Signal → Exit `11`
