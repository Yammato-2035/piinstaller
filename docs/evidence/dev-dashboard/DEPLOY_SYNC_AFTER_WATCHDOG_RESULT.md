# Deploy-Sync nach Watchdog — Ergebnis

**Datum:** 2026-05-28 (Wiederholung)  
**HEAD:** `5b4a874` | Watchdog-Implementierung: `2bf64b7`  
**Freigabe:** `DEPLOY_HELPER_SYNC_FREIGEGEBEN`

## Ergebnis: weiterhin blockiert

| Versuch | Ergebnis |
|---------|----------|
| 1 | `sudo systemctl start` → TTY/Passwort |
| 2 | `sudo -n systemctl start` → Passwort notwendig |

**Klassifikation:** `deploy_helper_blocked_by_sudo_tty`

## Gate

| | Exit |
|---|------|
| vorher | 14 |
| nachher | 14 |

Kein Rescue. Kein manueller `cp` nach `/opt`.

## Operator (privilegiertes Terminal)

```bash
cd /home/volker/piinstaller
sudo systemctl start setuphelfer-deploy-helper.service
journalctl -u setuphelfer-deploy-helper.service -n 120 --no-pager
./scripts/check-runtime-deploy-gate.sh
```

Bei Exit 0: Live-API prüfen, Next Prompt → `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`.

Siehe auch `DEPLOY_SYNC_AFTER_WATCHDOG_OPERATOR_HANDOFF.md`.

JSON: `deploy_sync_after_watchdog_result_latest.json`
