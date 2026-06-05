# KB — DCC, Profil und Port-Fehler

## Ports (verbindlich)

| Rolle | Adresse |
|-------|---------|
| Backend/API | `127.0.0.1:8000` |
| UI/DCC | `127.0.0.1:3001` |
| DCC URL | `http://127.0.0.1:3001/?window=cockpit` |
| nginx/default | `127.0.0.1:8080` — **nicht** DCC |

## `Development Control nicht verfügbar` / `profile=release`

**Klassifikation:** `expected_release_profile_block`

| Prüfung | Erwartung unter release |
|---------|-------------------------|
| `/api/version` | HTTP 200 |
| `dev_control_enabled` | `false` |
| Dev-Routen | `404` `PROFILE_ROUTE_BLOCKED` |
| DCC funktional | **nein** — erwarteter Sicherheitszustand |

**Kein** Portfehler. **Kein** Backend-down (wenn `:8000` antwortet).

**DCC gilt erst grün** nach `local_lab` Live-Acceptance (HTTP 200 auf Dev-Routen, Cockpit erreichbar, release danach restored).

Evidence: `DCC_LIVE_ACCEPTANCE_RELEASE_BASELINE.md`, `dcc_live_acceptance_latest.json`

## Portverwechslung

**Klassifikation:** `known_operator_port_confusion`

Symptom: DCC oder API über `:8080` erwartet.  
`:8080` = nginx/Ubuntu-Default, nicht SetupHelfer-DCC.

## `local_lab` Live-Smoke blockiert

**Status:** `dcc_profile_switch_blocked` wenn sudo in Agent-Session fehlt.  
**Kein Fake-Green** für DCC.

Operator-Handoff: `DCC_LIVE_ACCEPTANCE_LOCAL_LAB_RESULT.md`
