# OpenAPI 500 – Ursache und Fix (Post-Merge Cleanup)

**Datum:** 2026-05-23  
**HEAD vor Fix:** `2a55584`

---

## Symptom

```http
GET /openapi.json → 500 Internal Server Error
GET /api/partitions/scan → 200 OK
```

Partitions-Endpunkte funktionierten per curl; Swagger/OpenAPI-Schema brach global ab.

---

## Isolierung

| Test | Ergebnis |
|------|----------|
| Partitions-only FastAPI-App (`partition_router`) | `openapi.json` **200** |
| Volle App (`app.openapi()`) | **500** |

**Fazit:** Ursache **nicht** im Partitions-Router (`backend/api/routes/partitions.py`).

---

## Traceback (lokal, Service-venv)

```
PydanticUserError: `TypeAdapter[typing.Annotated[setuphelfer_deploy_routes.DeployRescueOfflineBackupPlanRequest, ...]]` is not fully defined; you should define ... and call `.rebuild()` on the instance.
```

Modul: `backend/deploy/routes.py` (dynamisch als `setuphelfer_deploy_routes` geladen).

Endpoint: `POST /rescue/offline-backup-plan` mit Body `DeployRescueOfflineBackupPlanRequest`.

---

## Ursache

`from __future__ import annotations` in `deploy/routes.py` erfordert `model_rebuild()` für Pydantic-Modelle, die in Route-Signaturen verwendet werden.

Sechs neuere Rescue-Request-Modelle hatten **keinen** `model_rebuild()`-Aufruf (Lücke nach `DeployRescueReadonlyMountRequest`):

- `DeployRescueBootContextPreviewRequest`
- `DeployRescueOfflineBackupPlanRequest` ← erster Fehler in der Generierung
- `DeployRescueRestorePreviewPlanRequest`
- `DeployRescueRecoveryTargetValidationRequest`
- `DeployRescueBackupDiscoveryVerifyRequest`
- `DeployRescueRestorePreviewRequest`

---

## Korrektur

Datei: `backend/deploy/routes.py` – sechs `model_rebuild()`-Zeilen ergänzt (nach Zeile `DeployRescueReadonlyMountRequest.model_rebuild()`).

Keine Änderung an Partitions-Schreiblogik, Queue/apply bleibt Phase-2-Stub.

---

## Verifikation

| Prüfung | Vorher | Nachher |
|---------|--------|---------|
| `app.openapi()` (Workspace, venv) | 500 | **OK**, 418 Pfade |
| Partition-Pfade in Schema | n/a | 5 Routen unter `/api/partitions/*` |
| `GET /api/partitions/scan` (Runtime) | 200 | **200** |
| `GET /openapi.json` (Runtime) | 500 | **200** |
| Runtime-Gate | 0 | **0** |
| `py_compile` deploy/routes.py | — | OK |

**Deploy:** `sudo ./scripts/deploy-to-opt.sh` schlug fehl (sudo-Passwort). Fix manuell nach `/opt/setuphelfer/backend/deploy/routes.py` kopiert; uvicorn-Reload übernahm die Datei.

**pytest:** nicht in Service-venv installiert (unverändert).

---

## Test-Duplikat

| Datei | Entscheidung |
|-------|--------------|
| `backend/tests/test_partitions_api.py` | **gelöscht** (untracked, älter, 3 Basis-Tests) |
| `backend/tests/test_partitions_api_v1.py` | **kanonisch** (7 Tests inkl. OpenAPI-Pfade) |

---

## Schreibschutz

Unverändert aktiv: keine mkfs/parted/dd/mount in Partitions-API; Queue/apply Phase-2-Stub.
