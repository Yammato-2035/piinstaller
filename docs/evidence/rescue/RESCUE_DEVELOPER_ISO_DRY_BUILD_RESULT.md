# Rescue Developer ISO Dry-Build — Result

**Date:** 2026-05-31  
**HEAD:** e50f4b3  
**Branch:** main  
**Version:** 1.7.3.0  

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** (Exit 0) |
| Backend-Version-Gate | **OK** (Exit 0) |
| `/api/version` | project_version=1.7.3.0 |
| Clean Runtime | **yes** — 0 WIP-Matches in `/opt` |
| Dirty Workspace | 43 entries (unberührt) |

## Profile paths

| Profile | Root |
|---------|------|
| Developer | `build/rescue/profiles/developer` |
| Public | `build/rescue/profiles/public` |

## Guard script

```bash
./scripts/check-dev-agent-rescue-profile-guard.sh
```

**Result:** Exit **0** — developer valid, public auto-upload blocked.

## Dry-build manifest

| Field | Value |
|-------|-------|
| Path | `docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest.json` |
| Status | **review_required** |
| dry_build | true |
| real_iso_build | **false** |
| generated_iso | **false** |

### review_required rationale

Warning `prior_iso_artifacts_in_tree:33` — existing artifacts under `build/rescue/live-build/` from prior controlled builds. **No new artifacts** created by this dry-build run (`new_forbidden_count=0`).

## Developer profile (manifest)

| Field | Value |
|-------|-------|
| profile_id | rescue_developer_local_lab |
| agent_enabled | **true** |
| agent_mode | local_lab |
| auto_upload | **true** |
| server_url | http://127.0.0.1:8000 |
| ssh_allowed | **false** |
| write_actions_allowed | **false** |

## Public guard

| Field | Value |
|-------|-------|
| agent_enabled | **false** |
| auto_upload | **false** |
| mode | public_rescue |
| public_upload_safe | **true** |
| public URL in profile | absent (127.0.0.1 only) |
| token in profile | absent |

## Systemd (simulated)

| Field | Value |
|-------|-------|
| service | setuphelfer-dev-agent.service |
| enabled_in_developer_profile | true |
| enabled_in_public_profile | false |
| exec_start_safe | true |
| no_new_privileges | true |

## Forbidden artifact scan

| Check | Result |
|-------|--------|
| New ISO created this run | **no** |
| New IMG created this run | **no** |
| New squashfs created this run | **no** |
| chroot/debootstrap/lb build executed | **no** |
| Prior ISO in live-build tree | yes (33 prior, classified existing_prior) |

## Tests

| Suite | Result |
|-------|--------|
| `test_devserver_agent_rescue_iso_dry_build_v1` | 15 OK |
| `test_devserver_agent_*` (all) | 69 OK |

## Safety

No ISO, lb build, debootstrap, chroot, squashfs, xorriso, USB write, backup, restore, SSH, apt.

## Entscheidung

| Question | Answer |
|----------|--------|
| Dry-build guards passed | **yes** (profiles + public guard OK) |
| Blocking errors | **none** |
| Real Developer ISO build freigegeben | **yes** — mit Operator-Prompt; prior artifacts documented |

**Next prompt:** **RESCUE DEVELOPER ISO CONTROLLED BUILD WITH DEV AGENT PROFILE**

## References

- `docs/architecture/RESCUE_DEVELOPER_ISO_DRY_BUILD_CONTRACT.md`
- `docs/evidence/rescue/RESCUE_DEVELOPER_DRY_BUILD_STRUCTURE_SCAN.md`
- `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_1_7_3_0.md`
