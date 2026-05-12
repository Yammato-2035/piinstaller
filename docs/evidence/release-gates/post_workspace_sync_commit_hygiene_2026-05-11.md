# Post Workspace Sync — CI & Commit Hygiene (2026-05-11)

Analyse nach Workspace-Sync-Commit **`36d234b`** (`chore: workspace sync; Fix CI safe device external media test`).

## 1. CI-Lauf zu `36d234b`

| Feld | Wert |
|------|------|
| **run_id** | `25691681846` |
| **workflow** | `ci.yml` (Name: CI) |
| **branch** | `main` |
| **head_sha** | `36d234be5505ec92e51621dee52111db797176a3` |
| **status** | `completed` |
| **conclusion** | **`failure`** (GitHub Actions ≠ success → **kein „CI grün“**) |
| **created_at** | `2026-05-11T19:14:23Z` |
| **updated_at** | `2026-05-11T19:15:29Z` |
| **URL** | https://github.com/Yammato-2035/piinstaller/actions/runs/25691681846 |
| **Job** | `lint-and-test` |
| **Fehlgeschlagener Step** | **Pytest** (Step 8) |

### Erster CI-Fehler (`gh run view 25691681846 --log-failed`)

- **Test:** `tests/test_deploy_runner_permission_boundary_v1.py::TestDeployRunnerPermissionBoundaryV1::test_no_sudoers_file_written`
- **Exception:** `PermissionError: [Errno 13] Permission denied: '/etc/sudoers.d/setuphelfer-runner'`
- **Auslöser:** `self.assertFalse(Path("/etc/sudoers.d/setuphelfer-runner").exists())` — auf dem GitHub-Runner kann `Path.exists()` für Pfade unter `/etc/sudoers.d/` bei fehlenden Leserechten **mit PermissionError** scheitern (nicht nur `False`).
- **Einordnung:** **Neuer Blocker**, **nicht** der frühere Safe-Device-`/media/volker`-Pfad. Safe-Device-External-Media liegt in diesem Lauf **vor** dem Abbruch im Log nicht als Failure.

## 2. Commit-Hygiene (`36d234b`)

### Kurzstatistik (`git show --shortstat 36d234b`)

- **2562 files changed**, **54178 insertions(+), 81 deletions(-)**
- **Name-Status:** `1611` × `M`, `951` × `A`, **`0` × `D`**

### Mode-Changes (`git diff-tree --summary -r 36d234b | grep 'mode change'`)

- **1606** Zeilen `mode change 100644 => 100755` (überwiegend **falsches +x** für Nicht-Skripte).

Stichprobe Dateiendungen bei Mode-Only-Zeilen (Auszug aus Summary-Parsing):

| Endung (Häufigkeit) | Anmerkung |
|---------------------|-----------|
| svg, md, png, html, json, tsx, ts, py, … | Für typische Daten-/Quelltext-Dateien ist **100755 unsinnig** |
| sh (wenige) | **100755** kann für echte Shell-Skripte sinnvoll sein — separat prüfen |

### Inhalt vs. reine Modusänderung (`git show --numstat`)

- **1341** Zeilen mit `0\t0\t<file>` (in `numstat`: keine Zeilenänderung; deckt sich weitgehend mit der Mode-Welle / binären Einträgen ohne Textdiff).
- **1221** Zeilen mit nicht-trivialen Insert/Delete-Zahlen (echte Inhaltsänderungen oder Binärdateien mit erfasstem Delta — je nach Git-Version unterschiedlich).

### Artefakt-Check (Ziel: keine `.venv` / `node_modules` / … im Commit)

Befehl:

`git show --name-only 36d234b | grep -E '(^|/)(\.venv/|venv/|__pycache__/|node_modules/|…)'`

**Ergebnis:** Keine Treffer für die geprüften Muster → **Root-`.venv/` wurde nicht versioniert** (laut Commit-Message: aus Index entfernt + `.gitignore` ergänzt).

**Zusätzlicher Review-Hinweis (manuell):** Unter **`A backend/cache/deploy/`** wurden u. a. **`*.img`**, **`blk*`** und ähnliche Deploy-Cache-Dateien **neu hinzugefügt**. Das sind potenziell **große Binär-Artefakte**; fachlich klären, ob sie absichtlich im Repo liegen müssen (LFS, Größe, CI-Zeit) — **kein automatisches Löschen** in dieser Analyse.

## 3. Bewertung Mode-Change-Welle

- **Risiko Reviews:** Sehr hohes Rauschen im Diff (tausende `mode change`-Zeilen).
- **Risiko CI/Packaging:** Gering bis moderat — ausführbar macht Dateien nicht automatisch „gefährlich“, ist aber **unüblich** für `.md`/`.json`/`.html` und erschwert Audits.
- **Empfehlung (kein Sofort-Revert von `36d234b`):** Separater **Hygiene-Commit** nur auf Git-Ebene:
  - `git ls-files -s | awk '$1==100755 && $4 !~ /\.sh$/ {print $4}'` (Konzept; Regex anpassen)
  - oder gezielt: `git update-index --chmod=-x -- <path>` für alle Nicht-Skripte nach Allowlist
- **Nicht** ohne Liste und Review: `.sh`/Entrypoints explizit **von** `-x`-Entzug ausnehmen.

## 4. Optionaler Hygiene-Fix (Phase 5)

**In diesem Schritt nicht ausgeführt** (nur dokumentiert): Mode-Korrektur und ggf. Review der `backend/cache/deploy/*`-Binärdateien verdienen einen **eigenen**, kleinen, nachvollziehbaren Commit — nicht blind revertieren.

## 5. Evidence

Siehe aktualisierte Dateien unter `docs/evidence/release-gates/` und `docs/roadmap/STATUS_MATRIX.md` sowie dieses Dokument.

## 6. Nächster offener Blocker (CI)

- **P1:** `test_no_sudoers_file_written` — `PermissionError` bei `Path(...).exists()` unter `/etc/sudoers.d/…` auf GitHub Actions (Run **25691681846**).
