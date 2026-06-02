# Rescue-Agent Report-Ingest — Stub-Smoke Readiness

**Stand:** 2026-06-02  
**Status:** **blocked** (`rescue_agent_ingest_blocked_sudo_required`)

## Erfüllt (Voraussetzungen)

| Kriterium | Status |
|-----------|--------|
| Release-Restore nach Fleet | **ok** |
| Release blockiert Rescue-Agent | **belegt** |
| Fleet / DCC | **green** |
| profile_gate | **green** |
| Runtime-Drift | **yellow**, nicht blockierend |

## Nicht erfüllt

| Kriterium | Status |
|-----------|--------|
| Live-Ingest unter `local_lab` | **not_run** |
| Negative + Register + Valid Report | **not_run** |
| Rohlogs mit HTTP-Codes | **partial** (nur Baseline) |

## Freigabe

**`ready_for_rescue_agent_ingest_stub_smoke`** erst nach abgeschlossenem Operator-Smoke mit `status=ok` oder `review_required-safe`.

## Nächster Schritt

Operator: vollständiges Smoke-Skript in Terminal mit sudo — siehe `RESCUE_AGENT_REPORT_INGEST_STUB_SMOKE_RESULT.md`.
