# Fleet Session Phase 1 — Result

**Datum:** 2026-06-02
**HEAD vor Umsetzung:** `5bb72c8`
**Branch:** `main`

## Runtime-Gate / Testmodus

| Check | Ergebnis |
|-------|----------|
| `scripts/check-runtime-profile-deploy-gate.sh` | **OK** |
| `scripts/check-runtime-deploy-gate.sh` | **Exit 20** (`LEGACY_GATE_NON_PROFILE_AWARE`, informational) |
| `setuphelfer-backend.service` | `active` |
| `setuphelfer.service` | `active` |

Bewertung für diesen Auftrag: **`fleet_phase1_live_acceptance_passed`**.
Die vorherige `sudo`-Blockade wurde durch einen interaktiven Operator-Terminal-Schritt aufgelöst; die Live-Abnahme gegen `/opt/setuphelfer` wurde anschließend vollständig durchgeführt und abgeschlossen.

## Phase-1 Implementierungsstand

| Bereich | Ergebnis |
|--------|----------|
| Session-Contract | vorhanden (`local_qemu_smoke`, Status/Severity, Pflichtfelder) |
| Backend-State | vorhanden (`create/update/heartbeat/finish/list/get/summary/stale`) |
| Persistenz | vorhanden (`fleet_sessions.jsonl`, `fleet_sessions_latest.json`) |
| Read-only API + Wrapper-Write | vorhanden (`/api/fleet/sessions*`) |
| Wrapper-Instrumentierung | vorhanden (create, heartbeat loop, finish, fallback) |
| UI-Kachel „Lab Sessions“ | vorhanden (Telemetry-Tab, LED/Status/KVM/Serial/Guest) |

## Verifiziert (live + statisch)

- `qemu_exit_code=124` wird als `timeout` klassifiziert.
- `serial_size_bytes=0` wird als `serial_empty` Warning sichtbar (kein Auto-Fail).
- `guest_report_seen=false` bleibt sichtbar (`guest_report_missing`).
- Keine Control-Routen (`execute/start/stop/revive/control/ssh/remote`) im Fleet-Router.
- Host-Session ist vom Guest-Node konzeptionell getrennt.
- Live unter `local_lab` bestätigt: `/api/fleet/sessions*` erreichbar und genau ein manueller Host-Session-Lauf persistiert.
- Nach Rückschaltung auf `release`: `/api/fleet/sessions*` liefert `HTTP 404 PROFILE_ROUTE_BLOCKED`.

## Tests

- Backend pytest (fleet/rescue): **32 passed** (2026-06-03, statisch)
- Shell payload: `status=running` → `agent_state=alive` (2026-06-03)

## Heartbeat-Fix (2026-06-03)

| Problem | Fix |
|---------|-----|
| `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD` bei `status=running` | Backend ignoriert `running`, setzt `agent_state=alive`; Shell sendet kein invalid status mehr |
| Tests | `test_fleet_session_heartbeat_payload_v1.py` + Shell-Payload-Test |

| Test | Ergebnis |
|------|----------|
| `pytest tests/test_fleet_session_state_v1.py tests/test_fleet_session_api_v1.py -q` | **14 passed** |
| `bash -n scripts/rescue-live/run-qemu-developer-iso-smoke.sh` | **OK** |
| `bash -n scripts/rescue-live/fleet-session-api.sh` | **OK** |
| `frontend npm run typecheck` | **nicht möglich** (`Missing script: typecheck`) |

## Scope / Guardrails

- Kein ISO-Build
- Kein QEMU-Lauf
- Kein USB/dd/mount/mkfs
- Kein Backup/Restore
- Kein SSH-/Remote-Control
- Kein apt install/upgrade
- Backend-Restart nur mit Operator-`sudo` (durchgeführt)

## NDA / Push

| Feld | Wert |
|------|------|
| Repository visibility | `PUBLIC` (`Yammato-2035/piinstaller`) |
| Push allowed | **no** |
| Push durchgeführt | **no** |
| NDA risk | `blocked_public_repository_ndA_risk` |

## Nächster sinnvoller Schritt

Heartbeat-Statusvertrag angleichen:
1. Heartbeat-Payload (`status=running`) auf erlaubte Fleet-Statuswerte umstellen oder Statusfeld weglassen
2. optional API-Regressionstest fuer den Heartbeat-Pfad ohne QEMU
3. Push bleibt blockiert (`blocked_public_repository_ndA_risk`)

## Update 2026-06-02 (Static Contract Pass)

- Heartbeat-Contract erweitert: `agent_state` (`alive|booting|checking|degraded|stalled|finished`).
- `status=running` im Heartbeat wird nicht mehr als Session-Status erzwungen; Mapping auf `agent_state=alive`.
- Neue Regression: `backend/tests/test_fleet_session_heartbeat_payload_v1.py`.
- Scope bleibt statisch: kein ISO/QEMU/USB/Backup/Restore.
