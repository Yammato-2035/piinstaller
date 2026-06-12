# System Network Route Migration — G.2b

**HEAD:** nach G.2b · **Route:** `GET /api/system/network`

## Änderung

| Vorher | Nachher |
|--------|---------|
| Inline Demo-Expansion + `get_network_info()` + `_detect_frontend_port()` | `build_system_network_response(use_demo=...)` |

## Response (unverändert)

Top-Level-Keys: `status`, `ips`, `localhost`, `primary_ip`, `interfaces`, `warnings`, `source`, `hostname`, `frontend_port`, `backend_port`

## Verhalten

- Demo: feste Ports 3001/8000, expandierte interfaces (unverändert)
- Live: Port-Erkennung über Legacy-Adapter `_legacy_detect_frontend_port`
- Fehler → `{"status":"error","message":...}` HTTP 200 (unverändert)
- Logging in Route-Handler beibehalten
