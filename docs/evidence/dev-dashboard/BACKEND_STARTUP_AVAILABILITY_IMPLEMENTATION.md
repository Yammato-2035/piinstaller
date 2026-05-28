# BACKEND_STARTUP_AVAILABILITY_IMPLEMENTATION

## Ziel

Backend-Hang als harter, sichtbarer Fehler statt stiller `HTTP 000000`-Meldung.

## Umsetzung

- `/health` bleibt leichtgewichtig und liefert strukturierte Minimaldaten.
- Runtime-Gate unterscheidet jetzt explizit Hang (`Exit 17`) von generischer Unerreichbarkeit.
- Standalone-Banner zeigt bei Timeout/Hang klaren roten Backend-Fail-State.
- Frontend-Loader klassifiziert API-Timeout als `backend_hanging_timeout`.
- Neue Tests fuer Health-/Startup-Verhalten und Standalone-Fail-State.

## Runtime-Gate Vorher/Nachher

- Vorher: `check-runtime-deploy-gate: /api/version HTTP 000000`
- Nachher: `check-runtime-deploy-gate: backend_hanging_active_port_but_http_timeout (health=timeout api_version=timeout)`

## Bewertung

- `runtime_gate_blocked_static_analysis_only=true`
- Runtime bleibt blockiert, aber Fehlerbild ist jetzt eindeutig und reparierbar dokumentiert.
