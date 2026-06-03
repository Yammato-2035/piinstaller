# Runtime Ports Registry — Deploy Ingest Result

**Datum:** 2026-06-03  
**Deploy:** bereits vom Operator ausgeführt (Commit `2406e68` → `/opt`)  
**Ingest-Lauf:** Evidence + Readiness, kein erneuter Deploy

## Zusammenfassung

Die zentrale Port-/Profil-Registry ist **live** unter `/api/version` auf der produktiven Runtime (`release`, profile gate **green**).

| Rolle | Port / URL |
|-------|------------|
| Backend/API | `127.0.0.1:8000` |
| UI / DCC | `http://127.0.0.1:3001/?window=cockpit` |
| nginx (nicht DCC) | `127.0.0.1:8080` |
| QEMU Lab Proxy (Host) | `127.0.0.1:8001` |
| QEMU Gast Devserver | `http://10.0.2.2:8001` |

Unter **release** sind Dev-Routen (`/api/dev-dashboard/*`, `/api/fleet/*`, `/api/rescue-agent/*`) mit **404** `PROFILE_ROUTE_BLOCKED` gesperrt — erwartetes Verhalten, kein Gating-Bug.

Watchdog (`/opt/.../check-backend-health.sh`): **exit 0**, `overall_status=ok`, `runtime_ports_source=/opt/setuphelfer/config/runtime_ports.json`.

**QEMU-Readiness:** `runtime_ports_registry_qemu_readiness_latest.json` → **`status=ok`**. QEMU wurde in diesem Lauf **nicht** ausgeführt; Freigabe nur für den nächsten Operator-Smoke.

## Evidence-Kette

| Phase | Dokument |
|-------|----------|
| 0 | `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_PHASE0.md` |
| 1 | `RUNTIME_PORTS_REGISTRY_LIVE_CHECK.md` |
| 2 | `RUNTIME_PORTS_PROFILE_GATING_LIVE_CHECK.md` |
| 3 | `RUNTIME_PORTS_WATCHDOG_AFTER_DEPLOY_CHECK.md` |
| 4 | `RUNTIME_PORTS_FRONTEND_LIVE_REVIEW.md` |
| 5 | `RUNTIME_PORTS_REGISTRY_DEPLOY_TEST_RESULT.md` |
| 6 | `runtime_ports_registry_qemu_readiness_latest.json` |

## Nächster Schritt

```bash
./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh
```

Vor dem Smoke: Profil auf **`local_lab`** setzen (Preflight); danach **`release`** wiederherstellen. Port **8001** (Proxy) wird erst beim QEMU-Lauf relevant.

## Nicht ausgeführt

ISO-Build, lb build, QEMU, USB, Backup, Restore, apt, Deploy, Push.
