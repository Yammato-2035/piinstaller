# Frontend Profile Build — Ergebnis

**Datum:** 2026-05-31

## Build-Profile

| Profil | Vite `SETUPHELFER_FRONTEND_PROFILE` | Dev-Control-UI |
|--------|--------------------------------------|----------------|
| release | `release` | aus (`DevControlDisabledPage`) |
| local_lab | `local_lab` | an + Warnhinweis |

## Release-Build (`npm run build`)

- `ExternalDevelopmentControlCenter`: bei `!devControlUiEnabled` → Disabled-Seite
- `LabSessionsPanel`: rendert `null` wenn `!fleetSessionsUiEnabled`
- Dev-Diagnostics-Copy-Buttons: nur wenn `devDiagnosticsUiEnabled`

## Statische dist-Prüfung

- i18n-Strings (`devDashboard.labSessions.*`) bleiben im Haupt-Bundle (alle Locales gebündelt) — **kein** erreichbares UI im Release-Profil (Tree-Shake + Runtime-Guard).
- Bewertung: **gelb** (Strings in Chunk-Metadaten), UI-Ausschluss **grün**.

## Local-Lab-Build

- `Interne Entwicklungsdaten` und Lab-Sessions-Keys im Bundle: **ja** (erwartet).

## Offen

- Separates Cockpit-Entry-Bundle für strikte String-Exklusion (optional, nicht Teil dieses Laufs).
