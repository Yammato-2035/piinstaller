# Backend Release Restart — Port 8000 Diagnostic

**Datum:** 2026-06-03

## Operator-Symptom

Nach Release-Restore: `curl: (7) Failed to connect to 127.0.0.1 port 8000` auf `/api/dev-dashboard/backend-health`.

**Das ist kein Profilblock** — Connection refused = Backend/Port nicht erreichbar.

## Analyse

| Ursache | Bewertung |
|---------|-----------|
| `PROFILE_ROUTE_BLOCKED` | **nein** bei curl (7) |
| DCC „nicht verfügbar“ unter release | **erwartet** (UI-Meldung korrekt) |
| Typische Ursachen | `daemon_reload_required`, **restart_race** (sofortiger curl nach restart), transient `backend_not_listening` |

Journal (Agent): nicht vollständig lesbar ohne sudo.

## Referenz

Gleiches Muster: `BACKEND_DOWN_AFTER_RELEASE_RESTART_RESULT.md` — Deploy ohne `daemon-reload` / Retry-Fenster.

| **Status** | **restart_race** + **daemon_reload_required** (historisch); **recovered** zum Zeitpunkt Phase 0 |
