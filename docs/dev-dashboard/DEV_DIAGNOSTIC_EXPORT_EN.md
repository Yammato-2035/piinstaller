# Diagnostic export (Development Control Center)

## Purpose

Provide a **redacted**, copy-ready diagnostic block for lab/QEMU smokes — combining fleet session, autopilot result, serial excerpts, and devserver ingest hints.

## UI

Development Control Center → **Telemetry** → **Lab Sessions** → expand a session:

- **Copy summary**
- **Copy diagnostics JSON**
- **Copy markdown report**

Warning: *Internal development data. Do not share publicly.*

## API (local)

See `docs/architecture/DEV_DIAGNOSTIC_EXPORT_CONTRACT.md`.

## Read-only

No QEMU start/stop, backup, restore, or deploy actions via these routes.
