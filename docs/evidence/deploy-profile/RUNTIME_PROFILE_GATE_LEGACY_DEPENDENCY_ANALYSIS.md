# Runtime Profile Gate — Legacy-Abhängigkeit (Analyse)

**Datum:** 2026-05-31 · **HEAD:** `cea84e6`+

## Symptom

```
check-runtime-deploy-gate: /api/dev-dashboard/status HTTP 404
check-runtime-profile-deploy-gate: base gate failed exit=20
```

## Ursache

`check-runtime-profile-deploy-gate.sh` rief zuerst `check-runtime-deploy-gate.sh` auf. Das Legacy-Gate **erzwingt** `GET /api/dev-dashboard/status` → HTTP **200**.

Im **Release-Profil** blockiert die Middleware Dev-Routen absichtlich mit **404** — das ist korrekt, kein Fehler.

## install_profile=opt

- **Alt:** `get_install_profile()` in `install_paths.py` = Laufzeitort (`opt`/`repo`), nicht Capability-Profil.
- **Neu:** Capability-Profil über `SETUPHELFER_INSTALL_PROFILE`; `opt` wird zu `release` gemappt (`legacy_profile_opt_mapped_to_release`).
- `/api/version` enthält zusätzlich `runtime_install_location` (`opt`/`repo`).

## profile_gate_status=red (OpenAPI)

Audit nutzte **alle** registrierten `app.routes` — Dev-Dashboard-Routen sind im Code registriert, aber per Middleware **404**. Fix: Audit nur bei aktiver Capability bzw. HTTP **2xx** (Profil-Gate-Evaluator).

## Zusätzlich: dev_server auf Live-Runtime

`SETUPHELFER_DEV_SERVER_ENABLED=true` in systemd ließ `/api/dev-server/*` mit **200** antworten. Release-Profil ignoriert Dev-Overrides nach Code-Fix; **Redeploy** nach `/opt` erforderlich.

## Gültige Profile

`release`, `developer`, `local_lab`, `rescue_lab`, `production`
