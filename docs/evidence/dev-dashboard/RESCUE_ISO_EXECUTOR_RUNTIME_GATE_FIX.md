# Rescue ISO Executor Runtime Gate Fix

**Datum:** 2026-05-25  
**Git HEAD:** `27d790a`

## Gate-Befund

- `./scripts/check-runtime-deploy-gate.sh` → **Exit 14**
- Bedeutung laut Gate-Skript:
  - `deploy_drift: deploy_backend_files empfohlen`

## Vermutete und verifizierte Ursache

Die Runtime selbst ist erreichbar und konsistent in Version/Pfad, aber der installierte Stand unter `/opt/setuphelfer` ist fuer mindestens eine relevante Backend-Datei aelter als der Workspace.

Verifiziert:

- `/api/version` → `status=success`
- `project_version=1.7.1`
- `backend_runtime_path=/opt/setuphelfer/backend`
- `install_profile=opt`
- `app_edition=release`
- `systemctl is-active setuphelfer-backend.service` → `active`
- `systemctl is-active setuphelfer.service` → `active`

## Deploy-Drift-Befund

- `deploy_drift.status` → `yellow`
- `deploy_drift.suggested_actions` → `["deploy_backend_files", "restart_backend_manual"]`
- `deploy_drift.manifest_match` → `true`

Betroffener Pfad:

- `backend/app.py`

Reason laut API:

- `compared_by_size_mtime`

## Bewertung

- Workspace ist fuer den relevanten Backend-Pfad neuer als `/opt`
- Deployment-Manifest ist **nicht** der Blocker
- Es handelt sich **nicht** um einen Version-Mismatch
- Es handelt sich **nicht** um einen Runtime-Pfad-Fehler
- Es handelt sich **nicht** um einen Dienst-nicht-aktiv-Fall
- Es ist ein klarer **Deploy-fehlt**-Fall

## Entscheidung

**Deploy erforderlich:** ja

Naechste zulassige Aktion:

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

Danach erneut:

```bash
./scripts/check-runtime-deploy-gate.sh
```

Erwartung nach erfolgreichem Deploy:

- Gate Exit `0`
- danach API-Smoke fuer `/api/dev-dashboard/rescue-iso/*`
- danach UI-Smoke im Cockpit

## Deploy-Versuch aus dem Agenten

Versucht:

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

Ergebnis:

- **nicht ausgefuehrt**
- Grund: interaktives `sudo` benoetigt Terminal/Passwort

Rueckmeldung:

```text
sudo: ein Terminal ist erforderlich, um das Passwort zu lesen
sudo: Ein Passwort ist notwendig
```

## Abschlussstatus

- Runtime-Gate-Ursache: **klar identifiziert**
- Deploy-Fix technisch klar: **ja**
- Deploy durch Agenten moeglich: **nein, operator_required**
- Status: **deploy_pending_operator_required**
