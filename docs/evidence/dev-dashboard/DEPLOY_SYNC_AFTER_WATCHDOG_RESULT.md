# Deploy-Sync nach Watchdog — Ergebnis

**Datum:** 2026-05-28  
**HEAD:** `2bf64b7`  
**Operator-Freigabe:** `DEPLOY_HELPER_SYNC_FREIGEGEBEN` (gesetzt)

## Ergebnis: blockiert

```bash
sudo systemctl start setuphelfer-deploy-helper.service
# → sudo: ein Terminal ist erforderlich, um das Passwort zu lesen
```

**Klassifikation:** `deploy_helper_blocked_by_sudo_tty`

- Kein manueller `cp` nach `/opt`.
- Kein zweiter Deploy-Versuch im Agent-Lauf.

## Gate

| | Exit |
|---|------|
| vorher | 14 |
| nachher | 14 |

## Operator-Handoff (privilegiertes Terminal)

```bash
cd /home/volker/piinstaller
sudo systemctl start setuphelfer-deploy-helper.service
systemctl status setuphelfer-deploy-helper.service --no-pager
journalctl -u setuphelfer-deploy-helper.service -n 120 --no-pager
./scripts/check-runtime-deploy-gate.sh
```

Bei Exit 0 optional:

```bash
curl -sS -m 10 http://127.0.0.1:8000/health | python3 -m json.tool
curl -sS -m 10 http://127.0.0.1:8000/api/version | python3 -m json.tool
```

Dann Roadmap `recommended_next` → `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`.

JSON: `deploy_sync_after_watchdog_result_latest.json`
