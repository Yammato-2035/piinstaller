# Rescue-Agent Report-Ingest — Stub-Smoke Readiness

**Stand:** 2026-06-02  
**Status:** **blocked**

## Blocker

| Ursache | Detail |
|---------|--------|
| **Profil-Guard** | Operator-curls in **`release`** → erwartetes `PROFILE_ROUTE_BLOCKED` |
| **sudo** | Guarded Script im Agent-Kontext ohne interaktives Passwort |

## Pflicht vor Live-Tests

```bash
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, dev_control_enabled, rescue_agent_router_status}'
# install_profile MUSS local_lab sein — sonst STOP
```

## Freigabe

`ready_for_rescue_agent_ingest_stub_smoke` erst nach guarded Operator-Script mit `status=ok`.

## Nächster Schritt

```bash
./scripts/rescue-live/rescue-agent-ingest-stub-smoke-operator.sh
```
