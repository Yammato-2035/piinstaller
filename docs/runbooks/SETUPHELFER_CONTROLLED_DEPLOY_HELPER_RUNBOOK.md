# Runbook - Setuphelfer Controlled Deploy Helper

## Zweck

Kontrollierter Deploy des validierten Workspace nach `/opt/setuphelfer`, ohne interaktives `sudo` im Agent-/Dashboard-Lauf.

## Sicherheitsgrenzen

- kein direkter Root-Deploy aus dem Backend
- kein `apt install/upgrade`
- kein USB-Write
- kein `dd`
- kein `mkfs`
- kein `parted`
- kein Backup
- kein Restore
- keine freien Shell-Kommandos

## Artefakte

- Root-Skript: `scripts/setuphelfer-deploy-helper-root.sh`
- systemd-Unit: `packaging/systemd/setuphelfer-deploy-helper.service`
- optionales sudoers-Beispiel:
  - `packaging/sudoers.d/setuphelfer-deploy-helper.example`

## Operator-Setup (manuell)

```bash
sudo cp packaging/systemd/setuphelfer-deploy-helper.service /etc/systemd/system/
sudo cp scripts/setuphelfer-deploy-helper-root.sh /opt/setuphelfer/scripts/setuphelfer-deploy-helper-root.sh
sudo chmod 0755 /opt/setuphelfer/scripts/setuphelfer-deploy-helper-root.sh
sudo systemctl daemon-reload
sudo systemctl status setuphelfer-deploy-helper.service
```

Optional fuer lokale Entwicklung, **nicht automatisch installieren**:

```bash
sudo cp packaging/sudoers.d/setuphelfer-deploy-helper.example /etc/sudoers.d/setuphelfer-deploy-helper
sudo chmod 0440 /etc/sudoers.d/setuphelfer-deploy-helper
```

## Dashboard-Workflow

1. `GET /api/dev-dashboard/deploy/status`
2. Deploy-Drift, Runtime-Gate und Helper-Status pruefen
3. Falls noetig:
   - `POST /api/dev-dashboard/deploy/operator-setup-commands`
4. Kontrollierten Deploy nur mit bestaetigtem Dialog anfordern:
   - `POST /api/dev-dashboard/deploy/request`
5. Deploy-Logs lesen:
   - `GET /api/dev-dashboard/deploy/logs`
6. Runtime-Gate nach dem Deploy erneut pruefen

## Persistente Evidence

- Status:
  - `/var/lib/setuphelfer/deploy-jobs/latest.json`
- Logs:
  - `/var/lib/setuphelfer/deploy-jobs/latest.log`

Fuer lokale Tests ohne `/var/lib`:

- `build/dev-dashboard/deploy-jobs/latest.json`
- `build/dev-dashboard/deploy-jobs/latest.log`

## Erfolgsdefinition

Ein Deploy gilt nur dann als erfolgreich, wenn:

1. `deploy-to-opt.sh` Exit `0` liefert
2. das nachgelagerte Runtime-Gate Exit `0` liefert

Alles andere bleibt sichtbar als:

- `failed`
- `blocked`
- `operator_required`

## Troubleshooting

### Helper nicht installiert

- Dashboard zeigt `operator_required`
- Setup-Kommandos ausgeben und manuell installieren

### Permission denied beim systemd-Start

- Polkit oder enge `sudoers`-Freigabe fehlt
- Dashboard bleibt `operator_required`

### Runtime-Gate bleibt Exit 14

- Deploy-Drift besteht weiterhin
- betroffene Dateien im Panel pruefen
- kein Runtime-Smoke als gruen melden

## Update-Check

Die vorbereitete Update-Karte prueft nur lokal:

- Workspace HEAD
- Runtime HEAD / Manifest
- Deploy-Drift
- lokale Versionskonsistenz

Es gibt **kein** automatisches Update und **keine** Paketmanager-Aktion.
