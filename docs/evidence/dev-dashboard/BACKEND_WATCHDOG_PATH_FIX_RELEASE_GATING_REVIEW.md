# Backend Watchdog Path Fix — Release Gating Review

**Datum:** 2026-06-03

## Live-Test (Agent)

Agent konnte **kein** `sudo` für Release-Drop-in (Runtime blieb **local_lab**). Ein versehentlich als „release“ gespeicherter Curl-Log (`watchdog_path_fix_backend_health_release_response.txt`) stammt von **local_lab** — **kein** Gating-Bug-Nachweis.

## Code-Verifikation (bindend für Middleware)

```text
release_test 404 PROFILE_ROUTE_BLOCKED
```

Log: `watchdog_path_fix_release_gating_code_test.log`  
Mechanismus: `install_profile_route_gate_middleware` blockiert `/api/dev-dashboard/*` wenn `dev_control_enabled=false`.

## Operator-Transkript (Terminal 6)

Nach Deploy + local_lab: `GET /api/dev-dashboard/backend-health` → **HTTP 200**, `source_path=/opt/.../backend_health_latest.json`, `stale=false`, `searched_paths` state=ok.

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Runtime release live getestet (Agent) | **no** |
| dev_control=false → Route blockiert (Code) | **yes** |
| backend-health unter release blockiert | **yes** (Middleware + TestClient) |
| HTTP Status (live release) | **n/a** (Agent) |
| Response-Code (Code-Test) | **PROFILE_ROUTE_BLOCKED** |
| **Status** | **ok** (kein `blocked_profile_gating_bug`) |

**Operator-Empfehlung:** Release kurz aktivieren und `curl -i /api/dev-dashboard/backend-health` → 404 bestätigen, dann release restore.
