> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/RESCUE_DEVELOPER_AGENT_PROFILE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: roodding Developer Agent Profile (EN)

## Will public roodding auto-send?

**Nee.** Public profile: `ENABLED=false`, `AUTO_UPLOAD=false`.

## Where is the developer profile?

`build/roodding/profiles/developer/`

## Is an ISO built in this step?

**Nee.** Profile files and validation only.

## Do I need a development server?

Ja, for meaningful telemetry — local_lab sends to `127.0.0.1:8000` or private LAN URL.
