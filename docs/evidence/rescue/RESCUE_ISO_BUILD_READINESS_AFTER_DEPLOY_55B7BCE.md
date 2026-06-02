# ISO-Precheck nach Deploy/Sync 55b7bce

**Stand:** 2026-06-02

| Kriterium | Status |
|-----------|--------|
| Fleet-Script-Fix in `/opt` | **ok** |
| Fleet Heartbeat Live Smoke | **ok** (neue Session) |
| Release-Profil wiederhergestellt | **blocked** (`release_restore_blocked_sudo_required`) |
| Runtime noch `local_lab` | **ja** |
| DCC-Port-Mapping | **green** |
| Deploy-Drift (legacy gate) | Exit 0 beim letzten Lauf unter `local_lab` |

## ISO-Precheck

**`blocked_by_release_restore`**

| Stufe | Status |
|-------|--------|
| Rescue-Agent Ingest Stub | `blocked_by_release_restore` |
| Controlled ISO build precheck | `blocked_by_release_restore` |

Erst nach Operator-Release-Restore + `check-runtime-profile-deploy-gate.sh` Exit 0 unter **release**:

→ `ready_for_rescue_agent_ingest_stub_smoke` (ggf. kurz `local_lab` nur für Ingest)  
→ `ready_for_controlled_iso_build_precheck`

Rescue bleibt **nicht grün** ohne echten ISO-/Boot-/USB-Nachweis. E2EE: contract_stub_only. nftables: preview_only_apply_false.

Nicht: ISO gebaut, USB bereit.
