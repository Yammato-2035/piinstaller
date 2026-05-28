# Backend Runtime Hang Triage Precheck

- Datum/Zeit (UTC): 2026-05-28T03:40:00Z
- Kontext: `main` auf Commit `f601080`
- Ziel: read-only Vorprüfung vor detaillierter Hang-Triage
- Sicherheitsgrenzen eingehalten: kein `sudo`, kein Restart, kein `kill`/`pkill`, kein Deploy/Rescue/Backup/Restore

## Phase-0-/Gate-Status

- `./scripts/check-runtime-deploy-gate.sh` -> Exit 11, `/api/version` HTTP `000000`
- `./scripts/check-backend-version-gate.sh` -> Exit 11, `/api/version` nicht erreichbar (curl timeout nach 2s)
- Ergebnis: Runtime-Gate bleibt `blocked_runtime_outdated_or_unreachable` im aktuellen Laufkontext.

## Kurzfazit Precheck

- Service ist laut systemd aktiv, API-Endpunkte antworten nicht.
- Folgeaktion: vollständige read-only Hang-Triage mit Prozess-/Socket-/HTTP-Evidence.
