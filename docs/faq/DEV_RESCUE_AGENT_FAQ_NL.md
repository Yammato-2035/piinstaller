> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/DEV_RESCUE_AGENT_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Development roodding Agent (EN)

## Does public roodding auto-send?

**Nee.** Default mode `public_roodding` blocks auto-upload.

## When does the agent send?

Only when `SETUPHELFER_DEV_AGENT_ENABLED=true` and mode `local_lab` with `AUTO_UPLOAD=true`.

## Is the agent alleen-lezen?

**Ja.** Allowlist commands only, Nee sudo, Nee mount/dd/mkfs.

## What if the server is down?

Reports are spooled under `docs/evidence/runtime-results/dev-agent-spool/`.

## SSH?

**Nee** — the agent does Neet use SSH.
