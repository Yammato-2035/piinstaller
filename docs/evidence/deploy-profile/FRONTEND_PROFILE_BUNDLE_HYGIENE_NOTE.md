# Frontend Profile Bundle Hygiene

**Datum:** 2026-05-31

## Bewertung: **gelb**

| Aspekt | Status |
|--------|--------|
| Release Dev-UI runtime-guarded | **grün** — `devControlUiEnabled`, Cockpit Disabled-Page |
| i18n-Strings im Haupt-Bundle | **gelb** — Keys bleiben in `dist` (alle Locales) |
| Runtime-Gate-Blocker | **nein** — UI nicht erreichbar bei Release-Build |

## Entscheidung

Funktional ausreichend für Release. Harte Bundle-Hygiene (separates Cockpit-Chunk ohne Lab-Strings) → Folgeprompt `FRONTEND_PROFILE_CODE_SPLITTING_AND_DEV_UI_BUNDLE_EXCLUSION`.
