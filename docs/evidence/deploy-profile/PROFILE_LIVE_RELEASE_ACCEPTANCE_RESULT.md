# Live-Abnahme Release-Profil

**Datum:** 2026-05-31 (aktualisiert)

## Profil-Gate (unabhängig)

| Prüfung | Ergebnis |
|---------|----------|
| `install_profile` | `release` |
| `/api/dev-dashboard/status` | **404** (korrekt) |
| `/api/fleet`, `/api/dev-diagnostics` | **404** |
| Profil-Gate vs. Legacy | **nicht** mehr Exit 20 durch Legacy-Kette |
| Profil-Gate Exit | **19** — `/api/dev-server` noch HTTP **200** (Override auf Live-Runtime, Redeploy offen) |

## Legacy-Gate

- Exit **20** — `LEGACY_GATE_NON_PROFILE_AWARE`, dev-dashboard 404 erwartet im Release

## Nach Redeploy (`install_profile.py` + Restart)

Erwartung: `dev_server_enabled=false`, `/api/dev-server/*` → 404, Profil-Gate Exit **0**
