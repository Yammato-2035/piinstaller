# QEMU Guest Agent Smoke — Backend Ingest Review

**Datum:** 2026-06-02

## Nach QEMU (nicht ausgeführt)

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Fleet Session neu | **no** (kein QEMU) |
| Rescue-Agent Session neu | **no** |
| Guest Report | **no** |
| Devserver-Discovery | **no** |

## Baseline release (readonly)

```
GET /api/fleet/sessions → 404 PROFILE_ROUTE_BLOCKED
GET /api/dev-server/summary → 404 PROFILE_ROUTE_BLOCKED
GET /api/rescue-agent/sessions → 404 PROFILE_ROUTE_BLOCKED
```

## Bewertung

**Status: blocked** — `qemu_smoke_blocked_by_profile`

Erwartete Findings bei fehlendem local_lab (Prior-Erfahrung): `guest_report_missing`, Dev-API unreachable from orchestration layer.
