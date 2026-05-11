# Anti-Regression-Rahmen – Abschlussbericht

_Stand: 2026-03-09_

## 1. Neu angelegte Dateien

| Datei | Zweck |
|-------|-------|
| `docs/development/anti_regression_rules.md` | Regeln, No-Gos, Prüffragen, kritische Bereiche |
| `docs/development/change_checklist.md` | Kurze operative Checkliste vor Änderungen |
| `docs/development/anti_regression_summary.md` | Dieser Abschlussbericht |
| `backend/tests/test_anti_regression.py` | Zwei minimale Prüfungen: Config-Pfad, doppelte Route |

## 2. Markierte kritische Bereiche

| Ort | Marker | Inhalt |
|-----|--------|--------|
| `backend/app.py` | REGRESSION-RISK | `_config_path()` – Runtime liest nur config.json |
| `backend/debug/config.py` | REGRESSION-RISK | Zentrales Debug, ENV PIINSTALLER_DEBUG_* |
| `scripts/install-system.sh` | REGRESSION-RISK | config.json als Source of Truth |
| `frontend/src/App.tsx` | REGRESSION-RISK | Neue Menüeinträge nur mit existierendem Ziel |

## 3. Ergänzte minimale Prüfmechanismen

| Mechanismus | Datei | Prüfung |
|-------------|-------|---------|
| Config-Pfad | `test_anti_regression.py` | `_config_path()` referenziert config.json |
| Doppelte Route | `test_anti_regression.py` | `POST /api/backup/verify` exakt einmal definiert |

## 4. Bereiche für manuelle Disziplin

- Boot-, Storage-, Hardware-Skripte (`scripts/*nvme*`, `*hdmi*`, `*freenove*`)
- Service-Templates (`pi-installer.service`, `pi-installer-backend.service`, `debian/*`)
- Sudo-Komponenten (`SudoPasswordDialog` vs. `SudoPasswordModal`)
- Log-Pfade (`pi-installer` vs. `piinstaller`)
- Frontend-Setup-Seiten (localhost-Links, API-Ziele)

---

## 10 regressionsgefährdetsten Stellen

| # | Stelle | Begründung |
|---|--------|------------|
| 1 | `backend/app.py` `_config_path()` | Zentrale Config-Quelle; Rückfall auf config.yaml wäre sofortige Regression |
| 2 | `backend/app.py` Route-Definitionen | Monolith mit vielen Routen; doppelte Definitionen schwer sichtbar |
| 3 | `scripts/install-system.sh` Config-Block | Installer könnte wieder config.yaml erzeugen |
| 4 | `backend/debug/config.py` Loader | ENV-Namen und Doku können erneut divergieren |
| 5 | `frontend/src/App.tsx` Navigation | Neue Pages ohne Backend/Route erzeugen tote Links |
| 6 | `frontend/src/pages/*Setup*.tsx` fetchApi | API-Aufrufe zu nicht implementierten Endpunkten |
| 7 | `backend/modules/*` vs. `backend/app.py` | Parallele Fachlogik; unbekannte Aufrufer |
| 8 | `pi-installer.service`, `pi-installer-backend.service` | Divergierende Service-Definitionen |
| 9 | `frontend/src/components/SudoPassword*.tsx` | Zwei Komponenten; dritte wäre weitere Dublette |
| 10 | `backend/app.py` Logging vs. `backend/debug` | Zwei Logging-Welten; Alt-Logging könnte wachsen |
