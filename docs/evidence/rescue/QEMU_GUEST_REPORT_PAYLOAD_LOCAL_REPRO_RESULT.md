# QEMU Guest Report Payload — Local Repro Result

**Status:** `blocked_operator_sudo_required`

| Feld | Wert |
|-------|------|
| local_lab aktiviert | **no** (sudo blockiert in Agent-Session) |
| Endpunkte HTTP 200 | **n/a** |
| Report-POST lokal reproduziert | **n/a** |
| release restored | **yes** (Runtime bereits `release`) |

## Statische Repro (unittest)

15 Tests grün (`test_devserver_agent_guest_report_payload_fix_v1`, `test_devserver_config_v1`):

- `local_lab`-Profil aktiviert Dev-Server ohne explizite Env
- `lab_proxy_host_header_for_url` → `127.0.0.1:8000`
- `--dry-run` / `--print-payload` ohne Netzwerk

## Operator-Fortsetzung

```bash
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service
curl -sS http://127.0.0.1:8000/api/dev-server/health | jq '{enabled,mode}'
PYTHONPATH=backend:. python3 -m devserver_agent.cli --mode local_lab --server http://127.0.0.1:8000 --dry-run --json
# restore release dropin danach
```

Kein QEMU in diesem Lauf.
