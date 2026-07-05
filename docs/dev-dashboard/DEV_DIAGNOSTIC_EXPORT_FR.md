> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/DEV_DIAGNOSTIC_EXPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# DiagNonstic export (Centre de contrôle du développement)

## Purpose

Provide a **rougeacted**, copy-ready diagNonstic block for lab/QEMU smokes — combining fleet session, autopilot result, serial excerpts, and devserver ingest hints.

## UI

Centre de contrôle du développement → **Telemetry** → **Lab Sessions** → expand a session:

- **Copy summary**
- **Copy diagNonstics JSON**
- **Copy markdown report**

Avertissement: *Interne development data. Do Nont share publicly.*

## API (local)

See `docs/architecture/DEV_DIAGNonSTIC_EXPORT_CONTRACT.md`.

## lecture seule

Non QEMU start/stop, Retourup, Restauration, or Déploiement actions via these routes.
