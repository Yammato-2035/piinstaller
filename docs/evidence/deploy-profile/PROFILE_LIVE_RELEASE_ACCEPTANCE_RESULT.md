# Live-Abnahme Release-Profil

**Datum:** 2026-05-31 (HTTP-000-Fix-Lauf)

## Ergebnis: **grün**

| Kriterium | Status |
|-----------|--------|
| `/api/version` stabil | **yes** HTTP 200 |
| `install_profile` | `release` |
| `manifest_profile` | `release` |
| Dev-Capabilities | alle **false** |
| Forbidden-Routen HTTP | alle **404** (inkl. `/api/dev-server/health`) |
| `check-runtime-profile-deploy-gate.sh` | **Exit 0** |
| Legacy-Gate | Exit **20** (informational) |

## Vorheriger Blocker

- HTTP **000** unmittelbar nach Restart (kein Retry)
- `/api/dev-server/health` **200** vor finalem Deploy von `install_profile.py`

## Local-Lab

**pending** — separater Operator-Auftrag (Drop-in `92-install-profile-local-lab.conf.example`).
