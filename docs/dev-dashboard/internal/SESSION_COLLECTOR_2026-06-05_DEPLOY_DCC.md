# Interne Session-Sammlung — Deploy-Fix & DCC (2026-06-05)

**Vertraulichkeitsstufe:** intern (Entwickler/Operator). **Keine Secrets.**

---

## Kontext

Nach mehreren DCC-/Telemetrie-Commits war `/opt/setuphelfer` erneut hinter dem Workspace. Symptom: profilabhängige Dev-Dashboard-Routen 404, obwohl Workspace-Code aktuell war.

Auslöser dieser Runde: **`dev_dashboard_compact_status.py`** fehlte in `/opt` → `GET /api/dev-dashboard/compact-status` → 404, Route nicht in `/openapi.json`.

---

## Allgemeiner Deploy-Befund (→ öffentliche KB)

Siehe [DEPLOY_TO_OPT_RUNTIME_SYNC.md](../../knowledge-base/deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md):

- rsync kopiert vollständig; Ursache war fehlender/veralteter Deploy + Manifest-Lücke + fehlende Post-Verify.
- Fix: `deploy_runtime_verify.py`, `verify_deploy_to_opt.py`, erweiterte `DEPLOY_MANIFEST_REL_PATHS`, Hooks in `deploy-to-opt.sh`.

---

## DCC-spezifisch (nur intern)

### Betroffene Routen / Module (Workspace-Stand)

| Modul / Route | Zweck |
|---------------|--------|
| `backend/core/dev_dashboard_compact_status.py` | Kompakt-Status-Aggregat für DCC |
| `GET /api/dev-dashboard/compact-status` | Ampel-Overview statt Rohdump |
| `backend/core/developer_capability.py` | Developer-Capability-Gate |
| `GET /api/dev-dashboard/capability-status` | Diagnose ohne Secrets |
| `backend/core/dev_dashboard_status_service.py` | Status-Service (Capability-Delegation Fix) |
| `backend/core/profile_deploy_manifest.py` | deploy_drift vs Developer-Exposure |
| `backend/rescue_telemetry/` | Telemetrie-Ingest (vom DCC getrennt geroutet) |

### Profil- vs Capability-Gate

- **Release-Profil:** `/api/dev-dashboard/*` standardmäßig blockiert (404) — erwartet.
- **Developer Capability:** Mit gültigem Developer-Token und `DCC_DEVELOPER_ENABLED` können Routen trotzdem erlaubt sein.
- **Legacy-Gate** (`check-runtime-deploy-gate.sh`): exit 20 im Release — **nicht** als Deploy-Fehler werten.
- **Profil-Gate** (`check-runtime-profile-deploy-gate.sh`): maßgeblich für Release-vs-lab.

### Nach Deploy prüfen (Operator, ohne Secrets zu loggen)

```bash
# OpenAPI
curl -sS http://127.0.0.1:8000/openapi.json | jq '.paths | keys[]' | grep -E 'compact-status|capability-status'

# Mit Developer-Token (Wert NICHT echo/loggen):
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H "X-Setuphelfer-Developer-Token: $(cat <operator-token-datei>)" \
  http://127.0.0.1:8000/api/dev-dashboard/compact-status

# Ohne Token: weiterhin blockiert im Release-Profil
curl -sS -o /dev/null -w '%{http_code}\n' \
  http://127.0.0.1:8000/api/dev-dashboard/compact-status
```

Erwartung mit Token: **200**. Ohne Token im Release: **404** (Profil-Block, kein Fake-Green).

### Dev-Server vs `/opt`

| Modus | Port | Hinweis |
|-------|------|---------|
| `npm run dev:cockpit` | 3001 (evtl. 3002+) | Browser-Cockpit |
| Tauri dev | 5173 strict | nur wenn Dev-Server läuft |
| Produktion | Backend 8000 | `frontend/dist` unter `/opt` |

Details: [../README.md](../README.md), [../PORTS_AND_PROFILES.md](../PORTS_AND_PROFILES.md).

### Evidence (technische Berichte)

- [DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md](../../evidence/dev-dashboard/DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md)
- [DEVELOPER_DCC_STATUS_ROUTE_CAPABILITY_FIX_RESULT.md](../../evidence/dev-dashboard/DEVELOPER_DCC_STATUS_ROUTE_CAPABILITY_FIX_RESULT.md)
- [DEVELOPER_DCC_TELEMETRY_DEPLOY_OPERATOR_HANDOFF.md](../../evidence/dev-dashboard/DEVELOPER_DCC_TELEMETRY_DEPLOY_OPERATOR_HANDOFF.md)

### Operator-Deploy (nur mit Freigabe)

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
python3 backend/tools/verify_deploy_to_opt.py \
  --workspace /home/volker/piinstaller \
  --runtime /opt/setuphelfer \
  --phase all
```

---

## Nächste Schritte (Roadmap, intern)

1. Operator-Deploy-Smoke (compact-status + capability-status)
2. `RESCUE_USB_BOOT_AND_WINDOWS_INSPECT_OPERATOR_RUN`
3. `DEVELOPER_DCC_FULL_ROUTE_CAPABILITY_AUDIT`
