> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/DEV_RESCUE_AGENT_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Development Secours Agent (EN)

## Does public Secours auto-send?

**Non.** Default mode `public_Secours` blocks auto-upload.

## When does the agent send?

Only when `SETUPHELFER_DEV_AGENT_ENABLED=true` and mode `local_lab` with `AUTO_UPLOAD=true`.

## Is the agent lecture seule?

**Oui.** Allowlist commands only, Non sudo, Non mount/dd/mkfs.

## What if the server is down?

Reports are spooled under `docs/evidence/runtime-results/dev-agent-spool/`.

## SSH?

**Non** — the agent does Nont use SSH.
