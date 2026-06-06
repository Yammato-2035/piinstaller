# FAQ: Runtime unter `/opt` — Deploy und fehlende Backend-Dateien

Allgemeine Betriebsfragen zu `deploy-to-opt.sh` und Workspace↔`/opt`-Drift.  
**Nicht enthalten:** Developer Control Center, Dev-Server, Tokens, profilabhängige Diagnose-Routen → siehe `docs/dev-dashboard/internal/`.

---

## Warum liefert eine neue API-Route 404, obwohl der Code im Repo ist?

Fast immer, weil **die produktive Runtime unter `/opt/setuphelfer` älter ist als der Workspace**. FastAPI lädt nur den Code aus `/opt`. Wenn dort das Modul oder die Route in `app.py` fehlt, erscheint die Route nicht in `/openapi.json` und antwortet mit 404.

**Prüfen:** `sha256sum` Workspace vs `/opt` für betroffene Dateien; `/openapi.json` auf den Pfad prüfen.

---

## Kopiert `deploy-to-opt.sh` alle Backend-Module?

Ja. `rsync` überträgt den **gesamten** Repo-Baum nach `/opt/setuphelfer`. Ausgeschlossen sind nur u. a. `.git`, `node_modules`, `venv`, `__pycache__`, `.env`, `dist`, `target` — **nicht** einzelne `backend/core/*.py`.

Untracked Dateien im Quellverzeichnis werden ebenfalls kopiert.

---

## Warum hat deploy_drift die fehlende Datei nicht gemeldet?

`deploy_drift` vergleicht eine **Whitelist** (`DEPLOY_MANIFEST_REL_PATHS`), nicht jeden Dateibaum. Fehlten neue Module in dieser Liste, konnte die Drift-Erkennung sie übersehen, obwohl `/opt` veraltet war.

**Abhilfe:** Whitelist erweitert; nach Code-Änderungen Manifest erzeugen:

```bash
python3 backend/tools/generate_deploy_manifest.py
```

---

## Was passiert nach dem Deploy neu (2026-06)?

`deploy-to-opt.sh` prüft automatisch:

1. **Nach rsync:** Kritische Backend-Dateien existieren in `/opt` und stimmen per SHA256 mit der Quelle überein (wenn in der Quelle vorhanden).
2. **Nach Backend-Restart:** Erwartete Routen sind in `/openapi.json` registriert.

Schlägt eine Prüfung fehl, endet der Deploy mit Exit ≠ 0.

Manuell:

```bash
python3 backend/tools/verify_deploy_to_opt.py \
  --workspace /path/to/workspace \
  --runtime /opt/setuphelfer \
  --phase all
```

---

## Muss ich nach Deploy noch manuell `systemctl restart` ausführen?

Nein, wenn `sudo ./scripts/deploy-to-opt.sh` **erfolgreich** durchläuft — das Skript startet `setuphelfer-backend` und `setuphelfer` neu. Nach Unit-/Drop-in-Änderungen ist **`daemon-reload`** vor dem Restart erforderlich (macht das Skript).

---

## Warum schlägt Deploy in Cursor/Agent-Sessions fehl?

`sudo` benötigt oft ein interaktives Passwort (kein TTY). Das ist **kein Code-Fehler**. Lösung: Deploy im Operator-Terminal ausführen oder `setuphelfer-deploy-helper.service` nutzen.

---

## Welche Gates vor Runtime-Arbeit?

| Gate | Zweck |
|------|--------|
| `check-backend-version-gate.sh` | `/api/version`, Workspace-Version |
| `check-runtime-profile-deploy-gate.sh` | Profil-aware (Release vs local_lab) |
| `check-runtime-deploy-gate.sh` | Legacy; im Release-Profil oft exit 20 (dev-dashboard 404 erwartet) |

Details: `docs/dev-dashboard/PHASE0_RUNTIME_GATE.md` (Phase-0-Checkliste).

---

## Verweise

- KB: [DEPLOY_TO_OPT_RUNTIME_SYNC.md](../knowledge-base/deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md)
- Runbook: [CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md](../runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_DE.md)
- Evidence: [DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md](../evidence/dev-dashboard/DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md)
