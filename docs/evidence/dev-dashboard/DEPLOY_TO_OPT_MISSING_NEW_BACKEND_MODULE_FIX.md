# DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX

**Datum:** 2026-06-05  
**Status:** Fix im Workspace; Operator-Deploy ausstehend (nur mit Freigabe)

## Befund

| Ort | `backend/app.py` | `backend/core/dev_dashboard_compact_status.py` | `/api/dev-dashboard/compact-status` |
|-----|------------------|-----------------------------------------------|-------------------------------------|
| Workspace | Route vorhanden | vorhanden | — |
| `/opt/setuphelfer` (vor Fix/Deploy) | andere SHA256 | **fehlte** | OpenAPI: nicht registriert → HTTP 404 |

Folge: FastAPI lud das Modul nicht; kein Token-/Frontend-Problem.

## Phase 0 (2026-06-05)

| Check | Ergebnis |
|-------|----------|
| `check-backend-version-gate.sh` | OK (exit 0) |
| `check-runtime-profile-deploy-gate.sh` | OK (exit 0) |
| Legacy `check-runtime-deploy-gate.sh` | exit 20 (Release-Profil: dev-dashboard 404 erwartet) |

## Analyse `scripts/deploy-to-opt.sh`

| Aspekt | Ergebnis |
|--------|----------|
| **Quelle** | `$1` oder Repo-Root des Skripts |
| **Ziel** | `/opt/setuphelfer` |
| **Mechanismus** | `rsync -a` gesamtes Repo |
| **Excludes** | `.git`, `node_modules`, `venv`, `__pycache__`, `*.pyc`, `.env`, `dist`, `target` |
| **backend/core-Filter** | **Keiner** — alle `.py` werden kopiert |
| **Untracked/neu** | rsync kopiert alle Dateien im Quellbaum, unabhängig von git status |

## Ursache (warum `dev_dashboard_compact_status.py` nicht in `/opt` war)

1. **rsync war nicht schuld** — kein Exclude auf `backend/core/*.py`.
2. **Wahrscheinlichste Ursache:** Deploy nach Commit mit Compact-Status **nicht ausgeführt** oder aus **veralteter Quelle** (anderer Checkout/HEAD als Workspace).
3. **Mitverschulden:** `DEPLOY_MANIFEST_REL_PATHS` kannte das neue Modul nicht → **deploy_drift** und Runtime-Gate erkannten die fehlende Datei **nicht**.
4. **Keine Post-Deploy-Prüfung:** `deploy-to-opt.sh` prüfte weder Datei-SHA256 noch OpenAPI nach Restart.

## Fix (Workspace)

1. **`backend/core/deploy_runtime_verify.py`** — kritische Pfade, SHA256-Vergleich Workspace↔`/opt`, `app.py`-Marker, OpenAPI-Pfad `/api/dev-dashboard/compact-status`.
2. **`backend/tools/verify_deploy_to_opt.py`** — CLI für Operator und Deploy-Skript.
3. **`scripts/deploy-to-opt.sh`** — nach rsync: `post-rsync`; nach Backend-Restart: `post-restart` (Deploy schlägt fehl, wenn Module fehlen).
4. **`backend/core/deploy_manifest.py`** — Whitelist erweitert um u.a. `dev_dashboard_compact_status.py`, `developer_capability.py`, `rescue_telemetry/*`.
5. **Tests:** `backend/tests/test_deploy_runtime_verify_v1.py`.

## Operator-Handoff (nach Freigabe)

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
```

Verifikation (keine Secrets in Logs):

```bash
test -f /opt/setuphelfer/backend/core/dev_dashboard_compact_status.py
sha256sum /home/volker/piinstaller/backend/app.py /opt/setuphelfer/backend/app.py
curl -sS http://127.0.0.1:8000/openapi.json | jq '.paths | keys[]' | grep compact-status
python3 backend/tools/verify_deploy_to_opt.py --workspace /home/volker/piinstaller --runtime /opt/setuphelfer --phase all
# Token-Smoke (Token aus lokaler Datei, nicht loggen):
curl -sS -o /dev/null -w '%{http_code}\n' -H "X-Setuphelfer-Developer-Token: $(cat /path/to/token)" \
  http://127.0.0.1:8000/api/dev-dashboard/compact-status
```

**Erwartung:**

- `/opt/.../dev_dashboard_compact_status.py` existiert, SHA256 = Workspace
- `/api/dev-dashboard/compact-status` in `/openapi.json`
- Mit Developer-Token: HTTP 200
- Ohne Token: Release-DCC weiter blockiert (Profil-Gate)

## Ist-Stand nach Workspace-Fix (ohne erneuten sudo-Deploy)

Lokale Prüfung zeigte bereits synchronen Stand (Deploy offenbar zwischenzeitlich gelaufen):

- `dev_dashboard_compact_status.py` in `/opt`: vorhanden
- `app.py` SHA256 Workspace = `/opt`
- OpenAPI: `/api/dev-dashboard/compact-status` registriert

Der Fix verhindert künftige stille Drifts durch fehlende Deploy-Läufe.

## Dokumentation (öffentlich vs. intern)

| Ebene | Datei |
|-------|--------|
| Wissensdatenbank | [DEPLOY_TO_OPT_RUNTIME_SYNC.md](../../knowledge-base/deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md) |
| FAQ | [RUNTIME_OPT_DEPLOY_FAQ_DE.md](../../faq/RUNTIME_OPT_DEPLOY_FAQ_DE.md) |
| Session-Protokoll | [CHAT_ZUSAMMENFASSUNG_DEPLOY_TO_OPT_2026-06.md](../../knowledge-base/CHAT_ZUSAMMENFASSUNG_DEPLOY_TO_OPT_2026-06.md) |
| DCC/Dev-Server (intern) | [internal/SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md](../../dev-dashboard/internal/SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md) |

Keine Secrets in diesen Dokumenten.
