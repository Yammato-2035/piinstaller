# DCC Live Acceptance — Release Baseline

**Datum:** 2026-06-05  
**HEAD:** `c36b707`

## Pflichtchecks (unter `release`)

| Check | Ergebnis |
|------|----------|
| `install_profile=release` | yes |
| `dev_control_enabled=false` | yes |
| Dev-Routen blockiert | `404` mit `code=PROFILE_ROUTE_BLOCKED` |
| Port `8000` erreichbar | `/api/version` → `200` |
| Port `3001` erreichbar | `http://127.0.0.1:3001/?window=cockpit` → `200` |
| Port `8080` (nginx) erkannt | `127.0.0.1:8080` → `200`, **nicht** SetupHelfer-DCC |

## Bewertung

**Ergebnis:** `release_block_expected`  

Hinweis: Dies ist **kein Nachweis**, dass das DCC unter release funktional ist. Unter `release` ist der Dev-Control-Bereich bewusst gesperrt (Sicherheitszustand).

