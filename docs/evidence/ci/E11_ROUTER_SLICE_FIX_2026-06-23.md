# E11 Router Slice Fix

## Ausgangsfehler
- **CI Run:** `28038420725`
- **Test:** `test_app_router_slice_e11.py::test_seventeen_routes_total`
- **Fehler:** `AssertionError: 20 != 17`

## System-Router bei HEAD `f4cbabe` (20 Routen)

| Methode | Pfad | Slice |
|---|---|---|
| GET | `/api/system/paths` | E10 |
| GET | `/api/system/devices` | E10 |
| GET | `/api/system/terminal-available` | E10 |
| POST | `/api/system/reboot` | E10 |
| POST | `/api/system/packagekit/stop` | E10 |
| GET | `/api/system/service-conflicts` | E11 |
| GET | `/api/system/resources` | E11 |
| GET | `/api/system/installed-packages` | E11 |
| GET | `/api/system/running-processes` | E11 |
| GET | `/api/system/security-config` | E11 |
| GET | `/api/system/updates` | E11 |
| GET | `/api/system/status` | E12 |
| GET | `/api/system/freenove-detection` | E12 |
| GET | `/api/system/asus-rog/fan/profiles` | E12 |
| GET | `/api/system/asus-rog/fan/status` | E12 |
| POST | `/api/system/asus-rog/fan/set-profile` | E12 |
| GET | `/api/system/asus-rog/detection` | E12 |
| POST | `/api/system/run-update-in-terminal` | **E13** |
| POST | `/api/system/run-mixer` | **E13** |
| POST | `/api/system/install-mixer-packages` | **E13** |

## Die 3 zusätzlichen Routen (17 → 20)

1. `POST /api/system/run-update-in-terminal`
2. `POST /api/system/run-mixer`
3. `POST /api/system/install-mixer-packages`

Alle drei sind in `test_app_router_slice_e13.py` als `E13_ROUTES` definiert; `test_twenty_routes_total` prüft den korrekten Gesamtstand.

## Entscheidung

**Test veraltet**, kein Code-/Router-Fehler.

Bei E12 wurde `test_eleven_routes_total` fälschlich auf `test_seventeen_routes_total` (17) umgestellt. E13 fügte +3 Routen hinzu und aktualisierte nur den E13-Test auf 20 — der E11-Test blieb bei 17 hängen.

## Fix

- `test_app_router_slice_e11.py`: kumulativen Exact-Count entfernen; E11-Subset wie E10 (`assertGreaterEqual(11)` + `E11_ROUTES` vorhanden).
- Kumulativer Contract: E12 `>= 17`, E13 `== 20`.

## Lokale Checks

| Check | Ergebnis |
|---|---|
| `pytest tests/test_app_router_slice_e11.py` | grün (gegen committed router: 20 Routen) |
| `pytest e11 + fix9 + anti_regression` | grün |
| `pip-audit` | grün |
| `npm audit --omit=dev --audit-level=high` | grün |

## Erwartetes CI-Ergebnis

- E11 bestanden; nächster möglicher Stopper außerhalb E11 (alphabetisch nach `-x`).
