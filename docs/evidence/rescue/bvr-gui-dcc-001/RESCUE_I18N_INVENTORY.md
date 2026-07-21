# Rescue i18n Inventory – PI-RS-BVR-GUI-DCC-001

Erfasst: **2026-07-21**

## Scope

Auto-E2E-Fortschrittsseite (`auto-e2e-progress.html`) und zugehörige Locale-JSON unter `scripts/rescue-live/image/locales/`.

## Locales

| Locale | Datei | Keys | Status |
|--------|-------|------|--------|
| de-DE | `de-DE.json` | 11 | present |
| en-US | `en-US.json` | 11 | present |
| fr-FR | `fr-FR.json` | 11 | present |
| nl-NL | `nl-NL.json` | 11 | present |

## Key-Parität

Referenz-Keyset (alle vier identisch):

`title`, `subtitle`, `status`, `phase`, `progress`, `run_id`, `payload`, `hint_running`, `hint_passed`, `hint_failed`, `device`

**Gesamt:** `complete` (Key-Parität erfüllt).

## Phase-Labels (HTTP-Server)

Zusätzlich in `setuphelfer-rescue-ui-http-server` → `PHASE_LABELS` für `/api/rescue/auto-e2e-status` (ASCII-only, nicht in Locale-JSON).

## Payload-Pfad (Runtime)

`/usr/share/setuphelfer/rescue/ui/locales/{de-DE,en-US,fr-FR,nl-NL}.json`

## Maschinenlesbar

Siehe [rescue_i18n_completeness.json](./rescue_i18n_completeness.json).
