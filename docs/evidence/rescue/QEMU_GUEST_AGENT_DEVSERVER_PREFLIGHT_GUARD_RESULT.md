# QEMU Guest Agent — Devserver Preflight Guard Result

**Datum:** 2026-06-03  
**Skript:** `scripts/rescue-live/qemu-guest-agent-smoke-operator.sh`

## Änderung

Neue Funktion `assert_devserver_preflight_ok()` — läuft **nach** `local_lab`-Aktivierung, **vor** QEMU-Start.

Prüft:

1. `GET /api/version` HTTP 200
2. `install_profile == local_lab` (bei `release` → `blocked_profile_route_blocked`)
3. `dev_control_enabled == true`
4. `GET /api/fleet/sessions` HTTP 200
5. `GET /api/dev-dashboard/status` HTTP 200
6. Port 8001: Warnung wenn belegt (Proxy startet im Smoke)
7. Exit **21** bei Block mit klaren Meldungen

`trap restore_release EXIT` unverändert.

## Pflichtbewertung

| Kriterium | Ergebnis |
|-----------|----------|
| Guard vorhanden | **yes** |
| local_lab zwingend | **yes** |
| dev_control_enabled zwingend | **yes** |
| fleet API 200 zwingend | **yes** |
| dev-dashboard API 200 zwingend | **yes** |
| QEMU startet bei release nicht | **yes** (Guard + Release-Trap) |
| Exit-Code bei blockiertem Devserver | **21** |

## Tests

- `bash -n scripts/rescue-live/qemu-guest-agent-smoke-operator.sh` — OK
- `backend/tests/test_qemu_guest_agent_devserver_preflight_guard_v1.py` — OK

**Status:** `ok`
