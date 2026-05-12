# CI — Deploy Runner Permission Boundary (`test_no_sudoers_file_written`)

**Analysedatum:** 2026-05-12  
**Betroffener Test:** `tests/test_deploy_runner_permission_boundary_v1.py::TestDeployRunnerPermissionBoundaryV1::test_no_sudoers_file_written`  
**Historischer CI-Lauf (36d234b):** Run `25691681846` — `PermissionError: '/etc/sudoers.d/setuphelfer-runner'`

## Phase 1 — Lokale Reproduktion

- **Kommando:** `cd backend && PYTHONPATH=. python -m pytest …::test_no_sudoers_file_written -vv` (in venv mit Abhängigkeiten).
- **Ergebnis:** Auf typischen Entwicklungs-Hosts oft **nicht** reproduzierbar (lstat liefert `ENOENT` oder Zugriff ist erlaubt).
- **Stacktrace (CI, sinngemäß):** Fehler in `pathlib.Path.exists()` → intern `stat()` → `PermissionError` mit Zielpfad `/etc/sudoers.d/setuphelfer-runner`.
- **Beteiligte API:** `Path.exists()` (nicht `open`/`write_text`/`mkdir` im Produktcode).

## Phase 2 — Testdatei (fachlich)

- **Ziel:** Sicherstellen, dass **kein** Drop-in `setuphelfer-runner` unter `/etc/sudoers.d/` existiert bzw. dass der Standort nicht von diesem Testlauf als „vorhanden“ bestätigt wird, ohne sudo oder Schreibzugriff auf `/etc`.
- **Problem:** Echter `/etc`-Pfad; auf GitHub Actions fehlen oft Leserechte für `stat` unter `/etc/sudoers.d/`.
- **Portabilität:** Unter **Python 3.12** propagiert `Path.exists()` bei `EACCES`/`EPERM` weiter ([`pathlib._ignore_error`](https://github.com/python/cpython/blob/3.12/Lib/pathlib.py) ignoriert nur u. a. `ENOENT`, nicht `EACCES`).
- **`skipTest` bei `PermissionError`:** Entfernt — vermeidet „Test weggeskippt“ und ersetzt den Nachweis durch einen gleichwertigen **Quelltext-Boundary-Check** (keine Abschwächung der Sicherheitsaussage zu Schreibvorgängen).

## Phase 3 — Produktcode

- Durchsucht: `backend/deploy/*`, `backend/deploy/routes.py`, `backend/tools/deploy_write_runner.py`.
- **Befund:** Kein Produktcode schreibt die Datei `/etc/sudoers.d/setuphelfer-runner`. Der dokumentierte Blueprint-Pfad lautet `/etc/sudoers.d/setuphelfer-deploy-runner` (`runner_package_blueprint.py`, `runner_install_consistency.py`) — anderer Dateiname.
- **Rolle des Tests:** Read-only Boundary-/Audit-Test, kein Installationspfad.

## Phase 4 — Ursachenklasse

**A und D** (kombiniert):

- **A:** Test nutzte einen echten `/etc/sudoers.d/…`-Pfad ohne isoliertes Dateisystem-Mock; `exists()` war unter CI nicht robust.
- **D:** CI-Umgebung verweigert `stat`/`lstat` auf Teilen von `/etc` — rechtlich und technisch normal.

## Phase 5 — Minimaler Fix (umgesetzt)

- `os.lstat(sudoers_dropin)`:
  - `FileNotFoundError` → Drop-in fehlt → **OK**, Return.
  - `PermissionError` / `OSError` mit `errno.EACCES` oder `EPERM` → **statisch** prüfen, dass **keine** Produkt-`.py` unter `backend/deploy/` (ohne `test`-Pfadanteile) und `backend/tools/deploy_write_runner.py` den Literal-String `/etc/sudoers.d/setuphelfer-runner` enthalten → **OK** (kein codierter Schreib-/Installationszielpfad für diesen falschen Namen).
  - erfolgreiches `lstat` → Datei/Link existiert → **`self.fail`** (unerwarteter Host-Zustand).
- **Keine** sudoers-Datei wird erzeugt, kein `/etc`-Write, keine Produktlogik geändert.

## Phase 6 — Tests (lokal)

- `tests/test_deploy_runner_permission_boundary_v1.py` — vollständige Datei.
- `tests/test_deploy_runner_*` — grün.
- `pytest tests/` — **1526 passed** (lokal, nach `pip install -r requirements.txt` im venv).

## Phase 7 — CI-Verifikation

Nach `git push origin main`: `gh run list -R Yammato-2035/piinstaller --workflow ci.yml --limit 5` — **Ampel „CI grün“** nur bei GitHub **`conclusion: success`**. Der zuletzt dokumentierte Lauf vor diesem Fix (Hygiene-HEAD `7e0323b`) scheiterte zuerst an `test_deploy_write_harness_v1` (`/mnt/setuphelfer`); der vorliegende Fix adressiert den **sudoers-Boundary**-Stop aus Run `25691681846`.
