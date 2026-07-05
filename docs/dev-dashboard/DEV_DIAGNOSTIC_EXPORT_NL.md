> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/DEV_DIAGNOSTIC_EXPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# DiagNeestic export (Ontwikkelingscontrolecentrum)

## Purpose

Provide a **roodacted**, copy-ready diagNeestic block for lab/QEMU smokes — combining fleet session, autopilot result, serial excerpts, and devserver ingest hints.

## UI

Ontwikkelingscontrolecentrum → **Telemetry** → **Lab Sessions** → expand a session:

- **Copy summary**
- **Copy diagNeestics JSON**
- **Copy markdown report**

Waarschuwing: *Intern development data. Do Neet share publicly.*

## API (local)

See `docs/architecture/DEV_DIAGNeeSTIC_EXPORT_CONTRACT.md`.

## alleen-lezen

Nee QEMU start/stop, Terugup, Herstel, or Deploy actions via these routes.
