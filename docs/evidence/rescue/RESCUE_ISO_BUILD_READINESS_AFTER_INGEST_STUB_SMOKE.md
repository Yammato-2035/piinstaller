# ISO-Precheck nach Ingest-Stub-Smoke

**Stand:** 2026-06-02

## Status

**`blocked_by_ingest_smoke_not_completed`**

Rescue-Agent-Ingest Live-Smoke: **blocked** (sudo / Operator-curls fehlen).

## ISO-Precheck

**Nicht freigegeben** bis Ingest `ok` oder `review_required-safe` **und** `release` nach Smoke belegt.

| Stufe | Status |
|-------|--------|
| Rescue-Agent Ingest Stub | **blocked** |
| Controlled ISO build precheck | **blocked_by_ingest_smoke_not_completed** |

## Guards

Kein ISO-Build in diesem Lauf.

## Nächster Schritt

1. Operator-Ingest-Smoke abschließen  
2. Release verifizieren  
3. Dann `ready_for_controlled_iso_build_precheck`
