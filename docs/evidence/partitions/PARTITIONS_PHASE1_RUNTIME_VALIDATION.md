# Partitionshelfer Phase 1 – Runtime-Deployment und Abnahme

**Datum/Zeit:** 2026-05-23T17:34Z (Abnahme nach Backend-Restart)  
**HEAD (vor Commit):** `f27bd10` auf `main`

---

## Abnahmeentscheidung

| Kriterium | Ergebnis |
|-----------|----------|
| Runtime-Gate | **Exit 0** (nach Deploy + Restart) |
| `GET /api/partitions/scan` | **HTTP 200**, JSON mit `disks`, `scanned_at` |
| OpenAPI `/openapi.json` | **HTTP 500** (gesamte App; vorbestehend) – Routen per Live-curl verifiziert |
| Frontend-Build | **grün** |
| py_compile | **grün** |
| pytest | nicht in Service-venv installiert (dokumentiert) |
| Schreibschutz Phase 1 | **aktiv** |
| Commit-Freigabe | **ja** (Runtime-API live) |

---

## Phase 0

- `active_backup_jobs`: `[]` – kein Deploy-Blocker.

---

## Deploy und Restart

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller` (Operator)
2. Erster Test: **404** – Prozess von 19:10, Deploy 19:23, **kein Restart**
3. `sudo systemctl restart setuphelfer-backend.service` (Operator)
4. Neuer Prozess PID ~17514, Start 19:33

---

## Runtime-Gate

| Lauf | Exit |
|------|------|
| Vor Deploy (Workspace-only) | 14 |
| Nach Deploy ohne Restart | 14, API 404 |
| **Nach Restart** | **0** |

```
check-runtime-deploy-gate: OK (Version, Pfad, deploy_drift/Manifest)
```

`GET /api/version` → 200, `backend_runtime_path`: `/opt/setuphelfer/backend`

---

## API-Smoke (Port 8000)

### Scan

```http
GET /api/partitions/scan → 200 OK
```

Antwort: strukturiertes JSON, 3 Disks, `scanned_at` gesetzt. **Keine Schreiboperation.**

### Safety-Check

```http
GET /api/partitions/safety-check?partition=nonexistent999&action=delete
→ 404 {"detail":"Partition 'nonexistent999' nicht gefunden"}
```

Read-only (keine Partition verändert).

### Queue / Apply

```json
GET /api/partitions/queue → {"actions":[]}
POST /api/partitions/queue/apply {"confirmed":true}
→ {"erfolg":0,"fehler":0,"blockiert":0,"message":"Keine ausführbaren Aktionen in der Queue (Phase 2)."}
```

---

## OpenAPI

`GET /openapi.json` → **500 Internal Server Error** (monolithische App-Schema-Generierung; nicht partitions-spezifisch).

Live-Endpunkte dennoch registriert (curl 200). `/docs` → HTTP 200.

Implementierte Routen (Code + Live):

- `GET /api/partitions/scan`
- `GET /api/partitions/safety-check`
- `GET /api/partitions/queue`
- `DELETE /api/partitions/queue`
- `DELETE /api/partitions/queue/{action_id}`
- `POST /api/partitions/queue/apply` (Phase-2-Stub)

---

## i18n

| | Pfad | Keys `partition.*` |
|---|------|-------------------|
| DE | `frontend/src/locales/de.json` | 43 |
| EN | `frontend/src/locales/en.json` | 43 |
| `sidebar.menu.partitions` | beide | |

Loader: `frontend/src/i18n/index.ts`

---

## Frontend / Backend Tests

- `npm --prefix frontend run build` → OK
- `python3 -m py_compile` partitions.py + app.py → OK
- `pytest` → nicht in `/opt/setuphelfer/backend/venv` (kein neues pip-Paket)

`backend/tests/test_partitions_api_v1.py` im Workspace (7 Fälle).

---

## Schreibschutz / tkinter

- Keine mkfs/parted/dd in API-Route.
- UI-Schreibaktionen disabled.
- `apps/partitionshelfer/` tkinter-Fallback unverändert.

---

## Commit

Nach diesem Lauf: gezieltes `git add` (kein `git add -A`), Message:

`feat(partitionshelfer): integrate read-only React phase 1`

---

## Post-Merge Cleanup (2026-05-23)

Siehe auch: `docs/evidence/partitions/PARTITIONS_OPENAPI_500_FIX.md`

| Punkt | Ergebnis |
|-------|----------|
| OpenAPI-500 Ursache | Fehlende `model_rebuild()` in `backend/deploy/routes.py` (Deploy-Rescue-Modelle), **nicht** Partitions-Router |
| Korrigierte Datei | `backend/deploy/routes.py` (+6 `model_rebuild()`) |
| `/openapi.json` vorher | **500** |
| `/openapi.json` nachher | **200** (Runtime, nach Datei-Sync nach `/opt`) |
| `/api/partitions/scan` | weiter **200** |
| Test-Duplikat | `test_partitions_api.py` gelöscht; kanonisch: `test_partitions_api_v1.py` |
| Runtime-Gate | **Exit 0** |
| Schreibschutz Phase 1 | **aktiv** (unverändert) |
| Deploy | `deploy-to-opt.sh` ohne sudo-Passwort blockiert; `routes.py` manuell nach `/opt` kopiert |
