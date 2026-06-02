# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| Fleet-Smoke | **ok** |
| Release-Restore | **ok** |
| Rescue-Agent Ingest Stub | **ok** |
| Runtime unter `release` | **ok** |

## Freigaben

| Stufe | Status |
|-------|--------|
| Rescue-Agent Ingest | **completed_ok** |
| **Controlled ISO build precheck** | **`ready_for_controlled_iso_build_precheck`** |
| ISO-Build | **not_approved** |

E2EE: contract_stub_only. nftables: preview_only_apply_false. Kein Rescue-Grün ohne ISO-/Boot-/USB-Nachweis.

Siehe: `RESCUE_ISO_BUILD_READINESS_AFTER_INGEST_STUB_SMOKE.md`
