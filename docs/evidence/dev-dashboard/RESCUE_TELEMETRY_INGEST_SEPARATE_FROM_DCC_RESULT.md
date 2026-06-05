# RESCUE_TELEMETRY_INGEST_SEPARATE_FROM_DCC — Ergebnis

**Datum:** 2026-06-05
**Status:** grün (Workspace-Tests) / gelb (Live-Ingest ohne Backend-Restart)

## Ziel erreicht

- `/api/dev-dashboard/*` bleibt unter Release `PROFILE_ROUTE_BLOCKED`
- Neuer Kanal: `GET /api/rescue/telemetry/health`, `POST /api/rescue/telemetry/v1/ingest`
- Ingest nur bei `RESCUE_TELEMETRY_INGEST_ENABLED=1` (sonst 503)
- Auth: Bearer / Header-Token / HMAC dokumentiert; mTLS-Konzept dokumentiert
- Store-and-forward Queue modelliert (`queue/`, `received/`, `acks/`)
- ACK + `hash_match: true` Pflicht bei Erfolg
- Keine Secrets in Evidence; Privacy-Guard wiederverwendet
- WoL geprüft: sysfs `disabled` → Server **must be online before rescue run**

## Artefakte

| Bereich | Pfad |
|---------|------|
| Core | `backend/core/rescue_telemetry_ingest.py` |
| Router | `backend/rescue_telemetry/routers.py` |
| Route-Gate | `backend/runtime_governance/route_exposure.py` |
| Tests | `backend/tests/test_rescue_telemetry_ingest_v1.py` |
| Vertrag | `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md` |
| KB | `docs/knowledge-base/development/RESCUE_TELEMETRY_INGEST.md` |
| WoL | `docs/evidence/dev-dashboard/RESCUE_TELEMETRY_WOL_DEVSERVER_CHECK.md` |

## Tests

```bash
cd backend && python -m pytest tests/test_rescue_telemetry_ingest_v1.py tests/test_runtime_governance_route_exposure_v1.py -q
```

## Offen (Operator)

Live-Smoke am laufenden Backend: `RESCUE_TELEMETRY_INGEST_ENABLED=1` + Restart-Freigabe → Prompt `RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE`.

## Next Prompt

`RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE` (P1); parallel P0 `RESCUE_ISO_UEFI_X64_FAILURE_TRIAGE`.
