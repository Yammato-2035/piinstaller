# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| Fleet-Script-Fix in `/opt` | **ok** |
| Fleet Heartbeat Live Smoke | **ok** (neue Session) |
| Release-Profil wiederhergestellt | **blocked** (`sudo` für systemd-Drop-in) |
| Runtime noch `local_lab` | **ja** |

## ISO-Precheck

**`blocked_by_release_restore`**

Erst nach Operator-Release-Restore + Gate erneut:

→ `ready_for_rescue_agent_ingest_stub_smoke`  
→ danach `ready_for_controlled_iso_build_precheck`

Nicht: ISO gebaut, USB bereit.
