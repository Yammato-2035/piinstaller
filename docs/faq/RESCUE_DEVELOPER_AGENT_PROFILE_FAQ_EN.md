# FAQ: Rescue Developer Agent Profile (EN)

## Will public rescue auto-send?

**No.** Public profile: `ENABLED=false`, `AUTO_UPLOAD=false`.

## Where is the developer profile?

`build/rescue/profiles/developer/`

## Is an ISO built in this step?

**No.** Profile files and validation only.

## Do I need a development server?

Yes, for meaningful telemetry — local_lab sends to `127.0.0.1:8000` or private LAN URL.
