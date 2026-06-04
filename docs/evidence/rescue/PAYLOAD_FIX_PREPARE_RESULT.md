# Payload Fix — Prepare Result

**Status:** `prepare_ok` (Tree-Sync; ISO-Inhalt noch stale)

| Feld | Wert |
|------|------|
| `prepare_exit` | **0** |
| `rescue_build_profile` | `developer-qemu` |
| Serial SEND Marker (Profil-Quelle) | **yes** — `SETUPHELFER_DEVSERVER_AGENT_SEND_*` in `build/rescue/profiles/developer-qemu/.../setuphelfer-qemu-smoke-autopilot.sh` |
| `devserver_agent.cli` Aufruf | **yes** (`python3 -m devserver_agent.cli`) |
| PYTHONPATH | `/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue` |
| Host-Header | `127.0.0.1:8000` in curl + SEND_TARGET |
| Guest URL | `http://10.0.2.2:8001` |
| Autopilot-Wants | via prepare bundle |

**Hinweis:** Vorhandenes `binary/live/filesystem.squashfs` stammt vom Build **vor** `ddd502e` (Jun 3 23:24) — enthält noch alte `client.py` ohne Host-Header-Fix.
