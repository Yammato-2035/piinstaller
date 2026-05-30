# FAQ: Development Rescue Agent (EN)

## Does public rescue auto-send?

**No.** Default mode `public_rescue` blocks auto-upload.

## When does the agent send?

Only when `SETUPHELFER_DEV_AGENT_ENABLED=true` and mode `local_lab` with `AUTO_UPLOAD=true`.

## Is the agent read-only?

**Yes.** Allowlist commands only, no sudo, no mount/dd/mkfs.

## What if the server is down?

Reports are spooled under `docs/evidence/runtime-results/dev-agent-spool/`.

## SSH?

**No** — the agent does not use SSH.
