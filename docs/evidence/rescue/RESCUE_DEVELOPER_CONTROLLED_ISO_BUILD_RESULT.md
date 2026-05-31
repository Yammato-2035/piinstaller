# Rescue Developer Controlled ISO Build — Result

**Date:** 2026-05-31  
**HEAD Start:** 54e9ce1  
**Branch:** main  
**Version:** 1.7.3.0  
**Run-ID:** `rescue_developer_iso_20260531_095558`  

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** |
| Backend-Version-Gate | **OK** |
| `/api/version` | 1.7.3.0 |
| Clean Runtime | **yes** (0 WIP-Matches) |
| Dev-Server | enabled, local_lab, storage_ok |

## Prior artifacts

| Field | Value |
|-------|-------|
| Inventory | `docs/evidence/runtime-results/rescue/prior-artifacts/prior_rescue_artifacts_before_controlled_developer_iso_build.json` |
| Count | 28 |
| Prior ISO archived | `build/rescue/archive/prior-controlled-builds/rescue_developer_iso_20260531_095558/binary.hybrid.iso` |

## Preflight

| Field | Value |
|-------|-------|
| Path | `docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_preflight.json` |
| Status | **review_required** (prior artifacts inventoried) |
| Profile guard | **OK** (exit 0) |
| Developer profile in tree | **yes** |

## Build

| Field | Value |
|-------|-------|
| Entrypoint | `scripts/rescue-live/run-controlled-iso-build-with-logging.sh` |
| Profile | **developer** |
| Exit code | **30** |
| Status | **blocked** |
| Error | `blocked_requires_operator_sudo_policy` |
| Build started | **false** (`lb build` not executed) |
| ISO found | **false** |
| ISO SHA256 | **none** (no new ISO) |
| Log | `build/rescue/logs/controlled-iso-build/latest.log` |

### Blocker

Agent-Umgebung: kein TTY, kein `sudo -n`, nicht root → Policy-Guard exit **30**. Zusätzlich: root-owned `binary/` aus früherem Build verhindert `./auto/clean` ohne sudo.

## Developer profile proof (build tree prepared)

| Check | Result |
|-------|--------|
| `setuphelfer-dev-agent.env` in chroot includes | **yes** — `SETUPHELFER_DEV_AGENT_MODE=local_lab`, `AUTO_UPLOAD=true` |
| `setuphelfer-dev-agent.service` in chroot includes | **yes** — `ExecStart=python3 -m devserver_agent.cli --send` |
| Hook enables dev-agent service | **yes** (developer profile branch) |
| `rescue-developer-profile.json` marker | **yes** |
| SSH / write in manifest | **false** |

## Public guard proof

| Check | Result |
|-------|--------|
| Guard script | exit **0** |
| Public agent enabled | **false** |
| Public auto_upload | **false** |
| Token in profile | absent |

## Safety

| Check | Result |
|-------|--------|
| USB write started | **false** |
| dd executed | **false** |
| Boot test | **false** |
| Backup/Restore | **false** |
| apt install/upgrade | **false** |

## Tests

| Suite | Result |
|-------|--------|
| `test_devserver_agent_*` | 69 OK (unchanged agent module) |

## Entscheidung

| Question | Answer |
|----------|--------|
| Controlled Developer ISO build green | **NO — BLOCKED** |
| Developer profile ready in build tree | **YES** |
| Real ISO build freigegeben | **NO** (operator sudo terminal required) |

**Next prompt:** **FIX RESCUE DEVELOPER CONTROLLED ISO BUILD**

Operator muss Build in interaktivem Terminal mit sudo ausführen (siehe Entrypoint Analysis).

## References

- `docs/evidence/rescue/RESCUE_DEVELOPER_CONTROLLED_BUILD_ENTRYPOINT_ANALYSIS.md`
- `docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_result.json`
- `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
