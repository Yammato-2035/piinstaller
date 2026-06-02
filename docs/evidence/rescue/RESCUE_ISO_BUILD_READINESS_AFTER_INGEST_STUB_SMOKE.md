# ISO-Precheck nach Ingest-Stub-Smoke

**Stand:** 2026-06-02

## Status

**`blocked_by_ingest_smoke_not_completed`**

Ingest-Stub-Smoke: **blocked** (`rescue_agent_ingest_blocked_sudo_required`).

## ISO-Precheck

**Nicht freigegeben** bis Ingest-Smoke ok/review_required-safe **und** `release` nach Smoke belegt.

## Vorherige Readiness (Deploy 55b7bce)

Release-Restore, Fleet, DCC, Drift yellow — weiterhin gültig als Voraussetzung, aber **Ingest-Lücke** blockiert Precheck-Freigabe.

## Guards

Kein ISO-Build, kein controlled ISO build in diesem Lauf.

## Nächster Schritt

1. Operator: Rescue-Agent Ingest Stub Smoke abschließen
2. Release wiederherstellen
3. Dann `ready_for_controlled_iso_build_precheck`
