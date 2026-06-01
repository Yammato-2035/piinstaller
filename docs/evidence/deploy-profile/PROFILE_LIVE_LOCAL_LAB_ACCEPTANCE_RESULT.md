# Live-Abnahme Local-Lab-Profil

**Datum:** 2026-05-31

## Durchführung

| Schritt | Ergebnis |
|---------|----------|
| `SETUPHELFER_INSTALL_PROFILE=local_lab` auf `/opt` | **nicht gesetzt** |
| Deploy + Restart | **blocked** — sudo erforderlich |

## Erwartung nach Operator-Deploy

- OpenAPI enthält `/api/fleet`, `/api/dev-diagnostics`, `/api/rescue-remote` (read-only)
- `public_exposure_allowed=false`
- Bind `127.0.0.1:8000` (kein `0.0.0.0` ohne Operator-Confirm)
- `check-runtime-profile-deploy-gate.sh` Exit **0** oder **yellow** (Frontend-Mismatch)

## Statische Abnahme

- Local-Lab registriert Dev-Router (Unit): **OK**
- Shell-Gate Local-Lab + erforderliche Pfade: **OK**
