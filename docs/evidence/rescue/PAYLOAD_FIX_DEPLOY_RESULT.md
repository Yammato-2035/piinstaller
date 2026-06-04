# Payload Fix — Deploy Result

**Status:** `review_required` (offizielles Deploy blockiert; partieller Backend-Sync)

| Feld | Wert |
|------|------|
| `deploy_exit` (official `sudo deploy-to-opt.sh`) | **1** — sudo: Passwort erforderlich |
| `deploy_helper` | nicht gestartet (NOPASSWD nur für User `setuphelfer`) |
| Partieller Sync | `devserver/config.py`, `devserver_agent/cli.py`, `devserver_agent/client.py` nach `/opt` (Gruppe `setuphelfer`, rsync/cp) |
| `/api/version` HTTP | **200** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| Fix-Marker in `/opt` | **yes** — `_profile_dev_server_defaults`, `--print-payload`, `--dry-run`, `lab_proxy_host_header_for_url` |

## Operator-Aktion erforderlich

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
# oder:
sudo systemctl start setuphelfer-deploy-helper.service
```

Ohne vollständiges Deploy bleiben Frontend/sonstige `/opt`-Dateien möglicherweise auf älterem Stand; Backend-Devserver-Fix ist für Guest-Ingest relevant.
