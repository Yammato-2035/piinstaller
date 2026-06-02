# ISO-Precheck nach Ingest-Stub-Smoke

**Stand:** 2026-06-02

## Status

**`blocked_by_ingest_smoke_not_completed`**

Ingest: **blocked** — Register/Report lief fälschlich unter `release`; guarded Script noch nicht erfolgreich.

## ISO-Precheck

Nicht freigegeben bis Ingest `ok` + `release_restored_after=true` belegt.

## Nächster Schritt

1. `./scripts/rescue-live/rescue-agent-ingest-stub-smoke-operator.sh` in Terminal 6  
2. Cursor-Ingest mit `smoke.log` + JSON  
3. Dann `ready_for_controlled_iso_build_precheck`
