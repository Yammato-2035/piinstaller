> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/RESCUE_DEVELOPER_AGENT_PROFILE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ: Secours Developer Agent Profile (EN)

## Will public Secours auto-send?

**Non.** Public profile: `ENABLED=false`, `AUTO_UPLOAD=false`.

## Where is the developer profile?

`build/Secours/profiles/developer/`

## Is an ISO built in this step?

**Non.** Profile files and validation only.

## Do I need a development server?

Oui, for meaningful telemetry — local_lab sends to `127.0.0.1:8000` or private LAN URL.
