# Deploy nach `/opt/setuphelfer` — Runtime-Sync und fehlende Backend-Dateien

**Zielgruppe:** Operatoren und Entwickler (allgemein, **ohne** Developer-Cockpit-/Dev-Server-Details).

**Struktur:** Symptom → Ursache → Nachweis → Maßnahme → Referenz.

---

## Symptom

- Workspace enthält neue Backend-Dateien (z. B. neues Modul unter `backend/core/`), aber unter `/opt/setuphelfer` fehlen sie.
- Betroffene API-Routen liefern **HTTP 404** (`{"detail":"Not Found"}`), obwohl der Code im Workspace committed ist.
- `sha256sum` von Workspace- und `/opt`-Dateien weicht ab (z. B. `backend/app.py`).

Das ist **kein** Frontend-Cache-Problem und **kein** reines Token-/Profil-Thema, solange die Route in `/openapi.json` gar nicht registriert ist.

---

## Was `deploy-to-opt.sh` wirklich tut

| Aspekt | Verhalten |
|--------|-----------|
| **Quelle** | Erstes Argument oder Repo-Root des Skripts |
| **Ziel** | `/opt/setuphelfer` |
| **Mechanismus** | `rsync -a` des **gesamten** Repo-Baums |
| **Excludes** | `.git`, `node_modules`, `venv`, `__pycache__`, `*.pyc`, `.env`, `dist`, `target` |
| **Filter auf `backend/core/*.py`** | **Keiner** — alle Python-Module im Quellbaum werden kopiert |
| **Git-Status** | **Irrelevant für rsync** — untracked Dateien im Quellverzeichnis werden mitkopiert |

**Folgerung:** Fehlende Dateien unter `/opt` entstehen fast nie durch rsync-Excludes, sondern durch **fehlenden oder veralteten Deploy-Lauf** oder **falsche Quelle**.

---

## Typische Ursachen

1. **Deploy nicht ausgeführt** nach dem Commit, der die neuen Dateien einführte.
2. **Deploy aus falscher Quelle** (alter Checkout, anderer Pfad als der aktive Workspace).
3. **Backend nicht neu gestartet** — seltener bei fehlender Datei; häufiger bei alter Route im Speicher trotz kopierter Datei.
4. **Deploy-Manifest-Lücke (Drift-Erkennung):** `DEPLOY_MANIFEST_REL_PATHS` kannte die Datei nicht → `deploy_drift` meldete keinen Hash-Abgleich für dieses Modul.
5. **Keine Post-Deploy-Prüfung:** Deploy endete mit Exit 0, obwohl kritische Module oder OpenAPI-Routen fehlten.

---

## Fix (Workspace-Stand ab 2026-06-05)

| Komponente | Zweck |
|------------|--------|
| `backend/core/deploy_runtime_verify.py` | Kritische Pfade, SHA256-Vergleich Workspace↔`/opt`, OpenAPI-Pfad-Check |
| `backend/tools/verify_deploy_to_opt.py` | CLI für Operator und Deploy-Skript |
| `scripts/deploy-to-opt.sh` | Nach rsync: `post-rsync`; nach Backend-Restart: `post-restart` — Deploy schlägt bei Fehler fehl |
| `backend/core/deploy_manifest.py` | Whitelist um wichtige Backend-Module erweitert |

---

## Nachweis (read-only)

```bash
# Phase 0 (Release-Profil: zusätzlich Profil-Gate)
./scripts/check-backend-version-gate.sh
./scripts/check-runtime-profile-deploy-gate.sh

# Datei in /opt?
test -f /opt/setuphelfer/backend/core/<modul>.py && echo OK || echo FEHLT

# SHA256 Workspace vs /opt
sha256sum /path/to/workspace/backend/app.py /opt/setuphelfer/backend/app.py

# Route in OpenAPI?
curl -sS http://127.0.0.1:8000/openapi.json | jq -r '.paths | keys[]' | grep '<route-segment>'

# Integrierter Verify (keine Secrets in Ausgabe)
python3 backend/tools/verify_deploy_to_opt.py \
  --workspace /path/to/workspace \
  --runtime /opt/setuphelfer \
  --phase all
```

Manifest neu erzeugen (Workspace):

```bash
python3 backend/tools/generate_deploy_manifest.py
```

---

## Maßnahme (Operator, mit Freigabe)

```bash
sudo ./scripts/deploy-to-opt.sh /path/to/workspace
```

Das Skript startet Backend und Web-UI neu und führt die Post-Deploy-Verifikation aus. Bei Fehlschlag: Journal prüfen (`journalctl -u setuphelfer-backend.service -n 200`).

**Hinweis:** Vollständiger Deploy erfordert interaktives `sudo`. Agent-Sessions ohne TTY-Passwort können Deploy blockieren — siehe Runbook `docs/runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md`.

---

## Verwandte Dokumente

| Dokument | Inhalt |
|----------|--------|
| [BUILD_RUNTIME_CONSISTENCY.md](../BUILD_RUNTIME_CONSISTENCY.md) | Source vs Build vs `/opt` |
| [operations/BACKEND_VERSION_UPDATE_GATE.md](../operations/BACKEND_VERSION_UPDATE_GATE.md) | Versions-Gate |
| [../../runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md](../../runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md) | Sauberer Deploy aus clean Checkout |
| [../../evidence/dev-dashboard/DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md](../../evidence/dev-dashboard/DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md) | Technischer Abschlussbericht (Evidence) |

**Developer-Cockpit / Dev-Server / profilabhängige Routen:** gesondert unter `docs/dev-dashboard/internal/` — **nicht** in dieser öffentlichen KB.
