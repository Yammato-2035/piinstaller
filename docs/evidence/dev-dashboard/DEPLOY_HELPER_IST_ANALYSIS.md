# Deploy Helper Ist-Analyse

**Datum:** 2026-05-25  
**Workspace:** `/home/volker/piinstaller`  
**HEAD:** `27d790a` (`main`)  
**Phase-0 Runtime-Gate:** Exit `14`

## Aktueller Befund

- `./scripts/check-runtime-deploy-gate.sh` liefert aktuell **Exit 14**.
- `deploy_drift.status`: `yellow`
- `betroffene Dateien`: `backend/app.py`
- `manifest_match`: `true`
- `suggested_actions`:
  - `deploy_backend_files`
  - `restart_backend_manual`

Damit ist der derzeitige Blocker kein "fake red", sondern ein echter Runtime-/Workspace-Drift: der Workspace enthaelt mindestens eine neuere Backend-Datei als `/opt/setuphelfer`.

## Aktueller Deploy-Ablauf

Der bisherige produktive Deploy laeuft ueber `scripts/deploy-to-opt.sh` und erwartet Root-Rechte. Das Skript:

1. validiert das Repo grob,
2. kopiert den Workspace nach `/opt/setuphelfer`,
3. aktualisiert Backend-Venv und Frontend-Build,
4. schreibt systemd-Units,
5. startet `setuphelfer-backend.service` und `setuphelfer.service` neu.

Der Ablauf ist heute fuer den Operator manuell beherrschbar, aber nicht sauber ueber das Dashboard steuerbar.

## Warum sudo bisher blockiert

- Der normale Backend-/Cursor-Lauf kann `sudo ./scripts/deploy-to-opt.sh` nicht interaktiv bedienen.
- Ein unprivilegierter FastAPI-Prozess darf nicht beliebig nach `/opt` schreiben.
- Ein direkter Root-Deploy aus dem Backend waere sicherheitlich zu breit, weil dann jede Fehlstelle im Backend potenziell auf Root-Aktionen erweitert werden koennte.

## Welche Dateien nach /opt muessen

`deploy-to-opt.sh` kopiert den freigegebenen Workspace-Baum nach `/opt/setuphelfer` und schliesst u. a. `.git`, `node_modules`, `venv`, `dist`, `__pycache__`, `.env` aus.

Fuer den aktuellen Runtime-Gate-Befund ist konkret mindestens diese Datei betroffen:

- `backend/app.py`

Der bestehende Deploy-Drift-/Manifest-Mechanismus bewertet darueber hinaus insbesondere folgende Runtime-relevanten Dateien:

- `backend/app.py`
- `backend/core/versioning.py`
- `backend/core/install_paths.py`
- `backend/core/dev_dashboard.py`
- `backend/tools/backup_runner.py`
- `packaging/helpers/setuphelfer-backup-starter.py`
- `config/version.json`
- `frontend/package.json`
- `frontend/src/components/ApiRuntimeConsistencyBanner.tsx`
- `frontend/src/pages/DevDashboardBody.tsx`

Mit dem neuen Deploy-Helper kommen zusaetzlich diese installierbaren Artefakte dazu:

- `scripts/setuphelfer-deploy-helper-root.sh`
- `packaging/systemd/setuphelfer-deploy-helper.service`
- optional: `packaging/sudoers.d/setuphelfer-deploy-helper.example`

## Welche Services neu gestartet werden

Der bestehende Deploy startet oder restarts:

- `setuphelfer-backend.service`
- `setuphelfer.service`

Alte Legacy-Units werden im Skript nur stillgelegt; relevant fuer den neuen kontrollierten Helper sind die beiden aktiven Setuphelfer-Services.

## Welche Logs / Evidence aktuell fehlen

Heute fehlt fuer den Deploy-Pfad eine Dashboard-lesbare, persistente Standardablage fuer:

- letzten Deploy-Job-Status als JSON
- letzten Deploy-Log als Text
- letzten Deploy-Exit-Code
- letzten Runtime-Gate-Exit vor/nach Deploy
- Helper-Installationsstatus / Operator-Setup-Bedarf

Genau diese Luecke blockiert die sichere Cockpit-Integration: das Dashboard sieht Drift, kann aber den kontrollierten privilegierten Schritt weder beauftragen noch auswerten.

## Sicherheitsrisiken eines direkten Backend-Root-Deploys

Ein direkter Root-Deploy aus dem normalen Backend-Prozess waere problematisch, weil er:

- Root-Schreibzugriff aus einem grossen, netzwerkfaehigen Prozess heraus eroefnen wuerde
- freie Shell-/Pfad-Eingaben schwerer begrenzbar machen wuerde
- Logging, Exit-Code und Parallelitaet schlechter absichern wuerde
- die Trennung zwischen read-only Dashboard und privilegierter Runtime-Aktion verwischen wuerde
- bei Fehlern zu "fake green" verleiten koennte, wenn Root-Schritte nicht sauber nachpruefbar sind

## Empfohlene Architektur

Empfohlen ist ein **root-gebundener `systemd`-Oneshot-Helper**:

- normaler Backend-Prozess bleibt unprivilegiert
- Backend fordert nur `systemctl start setuphelfer-deploy-helper.service` an
- die Root-Arbeit laeuft ausschliesslich ueber ein festes, validierendes Skript
- Status und Logs landen in persistenter Evidence:
  - `/var/lib/setuphelfer/deploy-jobs/latest.json`
  - `/var/lib/setuphelfer/deploy-jobs/latest.log`
- nach Deploy wird das Runtime-Gate erneut ausgefuehrt
- das Dashboard zeigt Erfolg, Fehler oder `operator_required` statt blind gruener Statusanzeigen
