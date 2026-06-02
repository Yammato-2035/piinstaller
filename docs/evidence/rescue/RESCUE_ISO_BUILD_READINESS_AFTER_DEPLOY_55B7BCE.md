# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| `release_restore_status` | **ok** |
| Fleet / DCC / Drift | **green / yellow** |
| Rescue-Agent Ingest Stub Smoke | **blocked** (sudo) |

## Freigaben

| Stufe | Status |
|-------|--------|
| Rescue-Agent Ingest Stub | **blocked** — Smoke nicht gelaufen |
| Controlled ISO build precheck | **blocked_by_ingest_smoke_not_completed** |

Siehe auch: `RESCUE_ISO_BUILD_READINESS_AFTER_INGEST_STUB_SMOKE.md`

Rescue bleibt nicht grün ohne ISO-/Boot-/USB-Artefakt. E2EE: contract_stub_only. nftables: preview_only_apply_false.
