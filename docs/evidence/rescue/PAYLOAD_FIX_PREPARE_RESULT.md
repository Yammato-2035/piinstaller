# Payload Fix — Prepare Result

**Status:** `prepare_ok`

| Feld | Wert |
|------|------|
| `prepare_exit` | **0** |
| Serial SEND Marker (Squashfs-Autopilot) | **yes** (9× `SETUPHELFER_DEVSERVER_AGENT_SEND_*`) |
| `devserver_agent.cli` | **yes** |
| PYTHONPATH | `/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue` |
| Host-Header | `127.0.0.1:8000` in SEND_TARGET |
| Guest URL | `http://10.0.2.2:8001` |
| Autopilot-Wants | enabled |
