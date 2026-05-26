# Version Bump 1.7.2 - Rescue / Notification

**Datum:** 2026-05-26
**Vorherige Version:** `1.7.1`
**Neue Version:** `1.7.2`

## Grund

Patch-Bump fuer zwei eng begrenzte inhaltliche Aenderungen:

- Rescue-ISO-RSVG-Fix als vorgelagerter Preflight-/Operator-Hinweis statt spaetem `LB_EXIT=127`
- Notification-E-Mail-Failure-Hardening fuer echtes Provider-Limit `554 5.7.0`, ohne Fake-Gruenstatus

Keine Release-Freigabe fuer ISO-Build, USB-Write oder Live-Boot ist damit verbunden.

## Betroffene Dateien

- `config/version.json`
- `frontend/package.json`
- `frontend/src-tauri/tauri.conf.json`
- `frontend/src-tauri/Cargo.toml`
- `package.json`
- `CHANGELOG.md`

## Einordnung

- vorheriger produktiver Notification-Stand: Commit `3adfc13`
- dieser Patch hebt nur die Version und den begrenzten Rescue-/Notification-Scope an
- kein ISO-Build in diesem Lauf
- kein USB-Write in diesem Lauf
