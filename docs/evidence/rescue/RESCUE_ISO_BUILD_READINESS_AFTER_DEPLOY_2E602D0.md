# ISO-Precheck-Readiness nach Deploy 2e602d0

**Stand:** 2026-06-02  
**ISO-Build:** nein

## Bewertung

| Kriterium | Status |
|-----------|--------|
| App-Bootstrap (committed) | ok |
| Router Registry / Startup Diagnostics | ok (Code) |
| Core Facades | ok |
| Rescue-Agent/Fleet (committed) | stub_ok |
| Deploy nach `/opt` | **ok** |
| Deploy-Drift (Code in `/opt`) | **ok** (Module live) |
| Runtime-Gate live | **yellow** (legacy gate exit 20; profil-Gate **0**) |
| DCC-Smoke | **blocked_by_profile_expected** |
| Fleet Heartbeat live | **blocked** (Profil `release`) |

## ISO-Precheck-Gesamtstatus

**`review_required`** (Deploy ok; Fleet-Live + optional DCC unter `local_lab` ausstehend)

Erst nach erfolgreichem `deploy-to-opt.sh` + Restart + grünem Drift-Gate + optional Fleet-Live-Smoke:

→ `ready_for_controlled_iso_build_precheck`

**Nicht** bedeutet: ISO gebaut, USB bereit, Rettungsstick fertig.
