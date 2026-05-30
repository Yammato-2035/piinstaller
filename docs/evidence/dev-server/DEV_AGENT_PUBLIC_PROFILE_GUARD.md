# Public Profile Guard — Development Agent

**Date:** 2026-05-30

## Rules enforced

| Check | Status |
|-------|--------|
| Public AUTO_UPLOAD | **false** in `build/rescue/profiles/public/environment/setuphelfer-dev-agent.env` |
| Public agent enabled | **false** |
| Public mode | **public_rescue** (not local_lab) |
| Dev-Agent local_lab in public manifest | **absent / false** |
| Public cloud URL | **none** — localhost placeholder only |
| Token in profile files | **none** |
| SSH allowed | **false** in both profiles |
| Write/backup/restore | **not enabled** |

## Public live-build

The existing public rescue ISO live-build tree does **not** include developer agent environment. Accidental auto-upload would require explicitly copying the developer profile — prevented by separate profile roots and guard script.

## Guard

`scripts/check-dev-agent-rescue-profile-guard.sh` — static validation, exit 0 when OK.
