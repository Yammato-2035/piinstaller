# TAURI_CONFIG_SCHEMA_FIX_AFTER_VERSION_PROJECTION

**Datum:** 2026-06-05

## Root Cause

`sync-version.js` schrieb `setuphelferProjectVersion` als **Top-Level-Feld** in `tauri.conf.json`. Tauri 2 validiert strikt gegen das JSON-Schema — zusätzliche Top-Level-Properties sind **nicht erlaubt** → `tauri build` bricht ab.

## Fix

- `setuphelferProjectVersion` aus `tauri.conf.json` entfernt; `sync-version.js` löscht das Feld künftig aktiv.
- Volle Projektversion in **`frontend/src-tauri/resources/setuphelfer-version.json`**, eingebunden über `bundle.resources`.
- `rename-tauri-bundle-artifacts.sh` liest **nur** `config/version.json` (kein Backend-Import).

## Commit / Push

- Commit: ja (nach Abschluss)
- Push: nein

## Verifikation

- `npm run tauri:build:projected` — **OK** nach Fix
- Bundle-Artefakte umbenannt: `SetupHelfer_1.7.3.1_amd64.deb`, `SetupHelfer-1.7.3.1-1.x86_64.rpm`, `SetupHelfer_1.7.3.1_amd64.AppImage`
- Zusätzlich: `deb.changelog` muss **Dateipfad** sein (nicht Inline-Text) — `deb-changelog.txt`
