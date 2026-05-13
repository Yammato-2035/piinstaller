# Backend-Update-Runbook (DE)

## A) Manueller Entwickler-/Testhost-Pfad (`/opt`)

1. **Backup** der betroffenen Dateien nach `/tmp/setuphelfer-deploy-backup-<timestamp>/` (`cp`/`install` nur mit Betreiber-`sudo`).
2. **`sha256sum`** *before*, *workspace*, *after* dokumentieren.
3. **Install** der freigegebenen Dateien (z. B. `app.py`, `core/safe_device.py`, `core/versioning.py`, `core/diagnostics/*.py`, **`config/version.json`**).
4. **`sudo systemctl restart setuphelfer-backend.service`**
5. **`./scripts/check-backend-version-gate.sh`** und **`curl -i http://127.0.0.1:8000/api/version`**
6. Bei Fehler: **Rollback** aus dem `/tmp`-Backup, erneuter Restart, Evidence aktualisieren.

**Kein** Backup-Job, **kein** Restore der Nutzerdaten, **kein** `dd`/`mkfs`.

## B) Paket-/Nutzer-Updatepfad (APT)

- **`apt update`** aktualisiert **nur** die Paketlisten — **installiert kein** neues Setuphelfer-Binary.
- Installation/Upgrade z. B.:  
  `sudo apt update`  
  `sudo apt install setuphelfer`  
  oder  
  `sudo apt upgrade setuphelfer`

**Voraussetzung:** reproduzierbares **`.deb`**, Paketname (z. B. `setuphelfer`), Versionierung, Maintainer-Skripte, systemd-Policy — siehe Roadmap `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`.

## C) Verbotene Muster

- Keine Einzeldatei-Kopien ohne Abhängigkeits- und `version.json`-Prüfung.
- Kein Test auf bekannt veraltetem `/opt`-Code.
- Kein Backup bei unklarem Runtime-Stand (Gate nicht grün).
