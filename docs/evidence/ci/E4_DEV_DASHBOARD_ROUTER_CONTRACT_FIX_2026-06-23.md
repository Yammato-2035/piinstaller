# E4 Dev-Dashboard Router Contract Fix

## Ausgangsfehler
- **CI Run:** `28040000612`
- **Test:** `test_app_router_slice_e4.py::test_no_subprocess_or_local_file_scanners`
- **Fehler:** `AssertionError: 'build_evidence_index' not found in dev_dashboard router`

## Contract

| Punkt | Befund |
|---|---|
| Alter Contract (Test) | Router-Quelltext enthält `build_evidence_index` |
| Neuer Contract (Router) | `from core.dcc_status_facade import build_dcc_evidence_index_api` |
| Fachliche Bedeutung | Evidence-Index-Route delegiert an DCC-Status-Facade (E.8/E.11); Facade liefert legacy Index-Shape für `GET /api/dev-dashboard/evidence-index` |
| Kompatibilität nötig? | Nein im Router — `build_evidence_index` bleibt in `core.dev_dashboard`; Facade ruft sie intern über `build_dcc_evidence_section` auf |
| Entscheidung | **Test aktualisieren** auf `build_dcc_evidence_index_api` + `dcc_status_facade` |

## Fix
- **Geänderte Dateien:** `backend/tests/test_app_router_slice_e4.py`
- **Safety:** `FORBIDDEN_PATTERNS` (kein subprocess/Scanner im Router) unverändert
- **Kein Router-/Core-Code geändert**

## Lokale Checks

| Check | Ergebnis |
|---|---|
| `pytest tests/test_app_router_slice_e4.py` | grün |
| `pytest e4 + e11 + fix9 + anti_regression` | grün |
| `pip-audit` | grün |
| `npm audit --omit=dev --audit-level=high` | grün |

## Erwartetes CI-Ergebnis
- E4 bestanden; nächster Stopper ggf. weiterer Router-Slice- oder Assertion-Test nach `-x`.
