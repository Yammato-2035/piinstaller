# Deploy plan (advisory)

## Summary

Setuphelfer can emit a **deploy plan** when no usable backup exists: it combines Inspect data, write-safety targets, and optional classification to answer whether a **fresh install** might be allowed, which **profiles** fit, and what would be **blocked** — without performing installs or disk writes.

## API

- `POST /api/deploy/plan` — returns `code` + `plan` object.
- Execute prep is documented separately in `DEPLOY_EXECUTE_PREP.md` and stays NO-OP in that phase.

## Safety

Plans defer to Write-Safety reason codes (`SAFETY_*`). Windows, dual-boot, system disks, and non-empty data disks lead to **blocked** deploy plans unless the scenario is clearly empty and consistent.
