# Backend Down After Release Restart — Test Result (Phase 7)

**Datum:** 2026-06-03

## Backend

| Lauf | Ergebnis |
|------|----------|
| `pytest -k "recent_evidence or dev_dashboard"` (breit) | **partial** — Collection-Errors in unrelated recovery tests |
| `pytest backend/tests/test_dev_dashboard_recent_evidence_v1.py` | **5 passed** |

`/opt` venv: kein `pytest` Modul (nicht ausgeführt gegen Runtime-venv).

## Frontend

| Lauf | Ergebnis |
|------|----------|
| `npm run build` | **ok** |
| `npm run test -- --run` | **54 passed** (13 files) |

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Backend tests | **partial** (targeted recent_evidence **ok**) |
| Frontend build | **ok** |
| Frontend tests | **ok** |
| **Status** | **partial** (wegen pytest collection noise, Kern-Fix grün) |
