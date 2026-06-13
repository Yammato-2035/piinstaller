# R.3 — Testmatrix Evidence

**Modul:** `backend/core/rescue_test_matrix.py`  
**Tests:** `backend/tests/test_rescue_test_matrix_r3.py` (3 Tests, OK)

## Verifikation

- Mindestens 18 Einträge (Ziel: 20 Bereiche)
- IDs `R3-BOOT-001` … `R3-NEXT-001` vorhanden
- Alle Statuswerte in erlaubter Menge

## Live-Aufruf

```bash
setuphelfer-rescue-evidence.py matrix
```

## Bewertungslogik (Kurz)

| Bereich | Grün wenn | Rot/Blocked wenn |
|---------|-----------|------------------|
| Persistenz | Stick writable, kein Fallback | RAM-Fallback ohne Warn-Akzeptanz |
| Restore-Gate | `write_actions_allowed: false` | Execute-Pfad erreichbar |
| MSI | DMI lesbar | — |
| Browser/Kiosk | Browser + Display | Browser fehlt (Build-Gap) |

## History

Jeder `write_rescue_test_matrix()`-Lauf appendiert eine Zeile in `rescue_test_matrix_history.jsonl`.
