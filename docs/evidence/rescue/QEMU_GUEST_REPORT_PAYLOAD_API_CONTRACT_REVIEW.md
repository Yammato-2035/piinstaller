# QEMU Guest Report Payload — API Contract Review

**Zielroute korrekt:** **yes** — `POST /api/dev-server/ingest/report`  
**Payload korrekt:** **yes** — `IngestReportRequest`: `{node, report}`; Pydantic `DevNodeSchema` + `DevReportSchema`  
**Session-/Run-ID Mapping:** **review_required** — Dev-Server ingest kennt keine Fleet-`session_id`; Matching über Report-Zähler + Serial  
**Registrierung erforderlich:** **no** (Node wird beim Ingest angelegt)  
**E2EE/Testmode:** **no** — kein E2EE auf Dev-Server-Ingest; Token optional  

## Wahrscheinliche Ursache (212528)

| Ursache | Bewertung |
|---------|-----------|
| `dev_server_disabled` unter local_lab | **primary** — Profil/Config-Desync |
| Fehlender Proxy-Host-Header auf POST | **secondary** — Client-Fix |
| `token_required_but_not_configured` | **secondary** — require_token default true |
| wrong_endpoint | **no** |
| fleet_rescue_session_mismatch | **no** (separate Schicht) |

**Klassifikation:** `missing_dev_server_runtime_enable_under_local_lab` + `proxy_post_host_header_missing`

## Schema (Pflicht)

- `report.report_id`, `report.node_id`, `report.lab_mode=local_lab`
- `node.node_id`, optional `node_kind`

OpenAPI unter `release` blockiert — Vertrag aus `backend/devserver/schemas.py` + `test_devserver_routes_v1.py`.
