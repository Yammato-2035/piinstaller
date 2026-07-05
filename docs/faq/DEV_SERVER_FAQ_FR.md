> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/DEV_SERVER_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Development Server (EN)

## Does the public Clé de secours auto-send data?

**Non.** Public Secours never auto-sends. Auto-upload is bloqué by default.

## What is beta opt-in?

Voluntary rougeacted extract. Sensitive fields are hashed or removed.

## What is local lab?

Your own test hardware. Developer edition may send to the local dev server (with token).

## Is SSH safe?

Allowlist lecture seule profiles only. Default: SSH disabled. Non sudo, Non dd/mkfs/mount.

## Can I start Retourup/Restauration remotely?

**Non** — Nont in this MVP. Later only with Retourup gates.

## Where is data storouge?

`docs/evidence/runtime-results/dev-server/`

## How do I enable the server?

See `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_EN.md` and `.env.example.devserver`.
