# Rescue Remote Agent Contract

**Agent:** `setuphelfer-rescue-remote-agent`

## Betrieb

- systemd-Service (später im Live-Image)
- `SETUPHELFER_REMOTE_ENABLED=1` erforderlich
- Default **disabled**
- `developer-qemu`: optional per Menü/QEMU-Lab
- Produktiv: nur nach Operator-Freigabe

## API (Development Server)

| Methode | Pfad |
|---------|------|
| POST | `/api/rescue-remote/register` |
| POST | `/api/rescue-remote/heartbeat` |
| GET | `/api/rescue-remote/jobs?agent_id=` |
| POST | `/api/rescue-remote/jobs/{id}/claim` |
| POST | `/api/rescue-remote/jobs/{id}/result` |
| POST | `/api/rescue-remote/disconnect` |

## Payload (Register)

Siehe User-Spezifikation — `security.remote_shell` und `controlled_write` müssen **false** sein.

## Stub

`scripts/rescue-live/setuphelfer-rescue-remote-agent.sh` — Python-Loop, allowlisted `subprocess.run` nur für feste Kommandolisten pro `runbook_id`.
