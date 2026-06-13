# R.3 — i18n / Dokumentations-Vollständigkeit

**Datum:** 2026-06-10

## UI-Änderungen

Keine Frontend-UI-Texte geändert — **kein** `frontend/src/locales` Sync erforderlich.

## Neue/aktualisierte Doku

| DE | EN |
|----|-----|
| `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3.md` | `..._EN.md` |
| `docs/knowledge-base/rescue/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3.md` | `..._EN.md` |
| `docs/faq/RESCUE_FAQ_DE.md` (neu) | `docs/faq/RESCUE_FAQ_EN.md` (neu) |
| `docs/faq/RESCUE_FAQ.md` (R.3-Abschnitt ergänzt) | EN-Abschnitte in bestehender FAQ unverändert |

## Architektur/Evidence (technisch, Sprache DE)

- `RESCUE_STICK_PERSISTENCE_R3.md`
- `RESCUE_TEST_MATRIX_R3.md`
- Evidence-Dateien unter `docs/evidence/rescue/*_R3.md`

## OpenAPI / Runbook

Keine API-Route-Änderungen in R.3 — OpenAPI unverändert.

Runbook-Hinweis: Stick-Operator nutzt `setuphelfer-rescue-evidence.py` und liest `matrix/rescue_test_matrix_latest.md`.

## Vollständigkeit

| Kriterium | Status |
|-----------|--------|
| DE/EN Architektur-Paar | ok |
| DE/EN KB-Paar | ok |
| DE/EN FAQ-Paar | ok |
| Rescue React i18n (`frontend/src/rescue/i18n`) | unverändert |
