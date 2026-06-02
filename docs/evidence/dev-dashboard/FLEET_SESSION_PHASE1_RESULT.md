# Fleet Session Phase 1 — Result

**Datum:** 2026-06-02
**HEAD vor Umsetzung:** `ea548fa`
**Branch:** `main`

## Runtime-Gate / Testmodus

| Check | Ergebnis |
|-------|----------|
| `scripts/check-runtime-deploy-gate.sh` | **Exit 20** (`LEGACY_GATE_NON_PROFILE_AWARE`) |
| `setuphelfer-backend.service` | `active` |
| `setuphelfer.service` | `active` |

Bewertung für diesen Auftrag: **`runtime_gate_blocked_static_only`**.
Daher nur statische Verifikation, keine Runtime-Smokes gegen Port 8000.

## Phase-1 Implementierungsstand

| Bereich | Ergebnis |
|--------|----------|
| Session-Contract | vorhanden (`local_qemu_smoke`, Status/Severity, Pflichtfelder) |
| Backend-State | vorhanden (`create/update/heartbeat/finish/list/get/summary/stale`) |
| Persistenz | vorhanden (`fleet_sessions.jsonl`, `fleet_sessions_latest.json`) |
| Read-only API + Wrapper-Write | vorhanden (`/api/fleet/sessions*`) |
| Wrapper-Instrumentierung | vorhanden (create, heartbeat loop, finish, fallback) |
| UI-Kachel „Lab Sessions“ | vorhanden (Telemetry-Tab, LED/Status/KVM/Serial/Guest) |

## Verifiziert (statisch)

- `qemu_exit_code=124` wird als `timeout` klassifiziert.
- `serial_size_bytes=0` wird als `serial_empty` Warning sichtbar (kein Auto-Fail).
- `guest_report_seen=false` bleibt sichtbar (`guest_report_missing`).
- Keine Control-Routen (`execute/start/stop/revive/control/ssh/remote`) im Fleet-Router.
- Host-Session ist vom Guest-Node konzeptionell getrennt.

## Tests

| Test | Ergebnis |
|------|----------|
| `pytest tests/test_fleet_session_state_v1.py tests/test_fleet_session_api_v1.py -q` | **14 passed** |
| `bash -n scripts/rescue-live/run-qemu-developer-iso-smoke.sh` | **OK** |
| `frontend npm run typecheck` | **nicht möglich** (`Missing script: typecheck`) |

## Scope / Guardrails

- Kein ISO-Build
- Kein QEMU-Lauf
- Kein USB/dd/mount/mkfs
- Kein Backup/Restore
- Kein SSH-/Remote-Control
- Kein apt install/upgrade
- Kein Backend-Restart ohne Operator-Freigabe

## NDA / Push

| Feld | Wert |
|------|------|
| Repository visibility | `PUBLIC` (`Yammato-2035/piinstaller`) |
| Push allowed | **no** |
| Push durchgeführt | **no** |
| NDA risk | `blocked_public_repository_ndA_risk` |

## Nächster sinnvoller Schritt

Operator-Freigabe für Runtime-Deploy + Backend-Restart, danach eine gezielte Live-Abnahme:
1. `GET /api/fleet/sessions`/`summary` in OpenAPI sichtbar
2. ein manueller QEMU-Smoke-Lauf (separater Auftrag) erscheint als Host-Session vor Guest-Ingest
3. Timeout-/serial_empty-Fall in UI verifizieren
