# QEMU Guest Report Payload — Send Path Review

**Status:** `send_path_identified`

## Sendepfad

| Feld | Wert |
|------|------|
| Modul | `devserver_agent.cli` → `cmd_send()` |
| Entry | `python3 -m devserver_agent.cli --mode local_lab --server http://10.0.2.2:8001 --send --json` |
| Ziel-URL (Gast) | `http://10.0.2.2:8001` (QEMU user-NAT Proxy → Host `127.0.0.1:8000`) |
| API-Route | `POST /api/dev-server/ingest/report` |
| Methode | `POST` |
| Content-Type | `application/json` |
| Body | `{"node": {...}, "report": {...}}` |
| Token-Header | `X-Dev-Server-Token` (optional; `require_token` default true → Block ohne Token) |

## Header (kritisch)

| Pfad | Host-Header |
|------|-------------|
| Autopilot health `curl` | `Host: 127.0.0.1:8000` ✓ |
| Agent `health_check` / `post_report` (vor Fix) | **kein** Lab-Host-Override → Proxy-Host `10.0.2.2:8001` |

## IDs / Mapping

| Feld | Quelle |
|------|--------|
| `run_id` | `SETUPHELFER_QEMU_SMOKE_RUN_ID` (Autopilot; oft `qemu_smoke_*` statt Operator-`fleet-*`) |
| `session_id` | Host: `fleet-${RUN_ID}` (Fleet); Gast sendet **keine** Fleet-Session-ID an Dev-Server |
| `node_id` | `devserver_agent.models.resolve_node_identity()` |
| `report_id` | Collector `new_report_id()` |

## Dev-Server Config vs. Profil

Router unter `local_lab` registriert (`dev_server_enabled=true`), aber `load_dev_server_config()` las `SETUPHELFER_DEV_SERVER_ENABLED` default **false** → Health-Validierung `dev_server_disabled` → CLI Exit 12/14 → `agent_send_failed`.

## Host-Ingest (Smoke)

`report_new` = `reports_last_24h` delta via `/api/dev-server/summary` (Host curl während `local_lab`).

Serial-JSON: einzeiliges `BEGIN {json} END` von systemd-ANSI **korrupt** → `guest_found=false`.
