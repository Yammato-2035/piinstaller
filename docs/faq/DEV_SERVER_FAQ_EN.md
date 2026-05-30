# FAQ: Development Server (EN)

## Does the public rescue stick auto-send data?

**No.** Public rescue never auto-sends. Auto-upload is blocked by default.

## What is beta opt-in?

Voluntary redacted extract. Sensitive fields are hashed or removed.

## What is local lab?

Your own test hardware. Developer edition may send to the local dev server (with token).

## Is SSH safe?

Allowlist read-only profiles only. Default: SSH disabled. No sudo, no dd/mkfs/mount.

## Can I start backup/restore remotely?

**No** — not in this MVP. Later only with backup gates.

## Where is data stored?

`docs/evidence/runtime-results/dev-server/`

## How do I enable the server?

See `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_EN.md` and `.env.example.devserver`.
