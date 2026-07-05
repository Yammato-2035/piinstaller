> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/DEV_SERVER_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Development Server (EN)

## Does the public rooddingsstick auto-send data?

**Nee.** Public roodding never auto-sends. Auto-upload is geblokkeerd by default.

## What is beta opt-in?

Voluntary roodacted extract. Sensitive fields are hashed or removed.

## What is local lab?

Your own test hardware. Developer edition may send to the local dev server (with token).

## Is SSH safe?

Allowlist alleen-lezen profiles only. Default: SSH disabled. Nee sudo, Nee dd/mkfs/mount.

## Can I start Terugup/Herstel remotely?

**Nee** — Neet in this MVP. Later only with Terugup gates.

## Where is data storood?

`docs/evidence/runtime-results/dev-server/`

## How do I enable the server?

See `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_EN.md` and `.env.example.devserver`.
