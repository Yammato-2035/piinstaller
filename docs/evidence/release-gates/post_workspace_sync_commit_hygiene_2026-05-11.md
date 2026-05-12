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

**Zusätzlicher Review-Hinweis (manuell):** Unter **`A backend/cache/deploy/`** wurden u. a. **`*.img`**, **`blk*`** und ähnliche Deploy-Cache-Dateien **neu hinzugefügt**. Diese wurden in der **Hygiene-Nachbearbeitung** (siehe unten) als **Klasse D** aus dem Git-Index entfernt und per `.gitignore` ausgeschlossen.

## 3. Bewertung Mode-Change-Welle

- **Risiko Reviews:** Sehr hohes Rauschen im Diff (tausende `mode change`-Zeilen).
- **Risiko CI/Packaging:** Gering bis moderat — ausführbar macht Dateien nicht automatisch „gefährlich“, ist aber **unüblich** für `.md`/`.json`/`.html` und erschwert Audits.
- **Empfehlung (kein Sofort-Revert von `36d234b`):** Separater **Hygiene-Commit** nur auf Git-Ebene:
  - `git ls-files -s | awk '$1==100755 && $4 !~ /\.sh$/ {print $4}'` (Konzept; Regex anpassen)
  - oder gezielt: `git update-index --chmod=-x -- <path>` für alle Nicht-Skripte nach Allowlist
- **Nicht** ohne Liste und Review: `.sh`/Entrypoints explizit **von** `-x`-Entzug ausnehmen.

## 4. Hygiene-Fix (ausgeführt)

Siehe Inventare:

- `docs/evidence/release-gates/mode_change_inventory_2026-05-11.json`
- `docs/evidence/release-gates/workspace_artifact_inventory_2026-05-11.json`

Kurz:

- **1606** Mode-Changes aus `36d234b` inventarisiert; **1602** Pfade im Git-Index auf **nicht ausführbar** zurück (`git update-index --chmod=-x`); **4** echte **`.sh`**-Skripte bleiben **755** (`git update-index --chmod=+x`, siehe JSON `keep_executable_755`). Auf Workspaces ohne Schreibrecht auf alle Dateien kann `git status` weiter **MM** (Index 644, Worktree noch +x) anzeigen — der committed Stand ist der Index.
- **`backend/cache/deploy/**`** und **`backend/job_rt_outside.json`** per `git rm --cached` aus dem Index entfernt (Dateien bleiben lokal unter `.gitignore` möglich); `.gitignore` um `backend/cache/deploy/` und `backend/job_rt_outside.json` ergänzt.
- **CI-Portabilität:** `tests/test_deploy_runner_permission_boundary_v1.py::test_no_sudoers_file_written` fängt `PermissionError` auf restriktiven Runnern ab (`skipTest` nur wenn `exists()` nicht statbar ist) — keine Produktlogik geändert.

**Hygiene-Commit:** Meldung `chore: clean workspace sync modes and artifacts` — SHA mit `git log -1` auf `main` ermitteln (nicht in dieser Datei gespiegelt, damit amend/rebase keine Drift erzeugt).

**Hinweis:** Ein fälschlich mitgestagtes Submodule **`ckb-next`** wurde vor dem Commit wieder aus dem Index genommen (`git restore --staged ckb-next`).

## 5. Evidence

Siehe aktualisierte Dateien unter `docs/evidence/release-gates/` und `docs/roadmap/STATUS_MATRIX.md` sowie dieses Dokument.

## 6. Nächster offener Blocker (CI)

- **Nach Hygiene-Push (HEAD `7e0323b`):** CI Run **25712570438** — **failure**; erster `-x`-Fehler: `tests/test_deploy_write_harness_v1.py::TestDeployWriteHarnessV1::test_execute_writes_limited_and_sha` — `PermissionError: '/mnt/setuphelfer'` beim `mkdir` in `setUp` (Runner hat kein beschreibbares `/mnt/setuphelfer`). URL: https://github.com/Yammato-2035/piinstaller/actions/runs/25712570438 — **kein „CI grün“**.
- **Referenz-Lauf zu `36d234b`:** Run **25691681846** (failure — `test_no_sudoers_file_written` / `/etc/sudoers.d`, siehe Abschnitt 1).
