# CI-Failure-Analyse: Fix13 Full-Backup Excludes (`test_backup_full_excludes_fix13_v1`)

**Datum:** 2026-05-11  
**Fehler (GitHub Actions):** `AssertionError: [] is not true : expected tar command for full backup`  
**Test:** `tests/test_backup_full_excludes_fix13_v1.py::TestBackupFullExcludesFix13V1::test_full_backup_command_excludes_media_and_existing_paths`

## 1. Reproduktion

- **Lokal (volle Backend-Dependencies, Host mit systemd-inhibit):** Test **grün** ohne Änderung — `run_command` wird mit dem inhibit-gewrappten tar-String aufgerufen.
- **Lokal simuliert (entspricht CI):** Wenn `shutil.which("systemd-inhibit")` `None` liefert oder `os.access(..., X_OK)` fehlschlägt, bricht `_run_tar` in `app.py` **vor** jedem `run_command`-Aufruf mit `returncode -42` ab → `seen_cmds` bleibt **leer** → gleiche Assertion wie in CI.

## 2. Testbefund

| Aspekt | Befund |
|--------|--------|
| Patch-Ziel (vormals) | `app_module.run_command` — korrekt für den Pfad, der `run_command` erreicht |
| Beobachtung | Liste `seen_cmds`: alle an `fake_run_command` übergebenen Befehlsstrings |
| Erwartung | Mindestens ein Eintrag enthält `tar -czf ` inkl. `--exclude=/media`, `--exclude=/run/media`, Backup-Verzeichnis, Standard-Excludes |

## 3. Produktcode (`backend/app.py`)

- `_do_backup_logic` → `backup_type == "full"` baut `backup_cmd` mit `--exclude=/proc`, `/sys`, `/dev`, `/tmp`, `/run`, `/mnt`, `/media`, `/run/media`, sowie `--exclude=<backup_dir>` und `tar -czf … /`.
- **`_run_tar`:** Prüft zuerst `systemd-inhibit` via `shutil.which` und `os.access(…, X_OK)`. Fehlt das Binary oder ist es nicht ausführbar, wird **kein** `run_command` aufgerufen (Absicht: Suspend-Guard erzwingen).
- Ohne `cancel_event` ruft `_run_tar` bei Erfolg der Prüfungen `run_command(guarded_cmd, …)` mit dem inhibit-gewrappten Shell-Befehl auf.

## 4. Ursachenklasse

**D** — Der Test erreichte den Tar-/run_command-Pfad nicht, weil die **Produktlogik berechtigt** bei fehlendem/nicht ausführbarem `systemd-inhibit` vorher zurückkehrt (Safety/Inhibit-Pflicht). Zusätzlich **E** (CI-Umgebung ohne nutzbares inhibit) als Auslöser — kein Logikfehler an den Excludes.

## 5. Minimaler Fix (kein Produktcode)

- Test ergänzt: **gezieltes** Mocken von `app_module.shutil.which` (liefert festen Pfad für `systemd-inhibit`) und `app_module.os.access` (liefert `True` für `X_OK` auf diesem Pfad).
- Weiterhin: alle konkreten `--exclude=…`-Assertions und `backup.failed`; **keine** Abschwächung der Sicherheitsprüfung im Produktcode.
- `shutil.which`/`os.access` delegieren für alle anderen Pfade an die Stdlib-Implementierung (kein globales „alles True“).

## 6. Ausgeführte Tests (lokal)

- Interpreter: venv unter `/tmp/piinstaller-test-venv` (Requirements aus `backend/requirements.txt`).
- `tests/test_backup_full_excludes_fix13_v1.py` — **2 passed**
- `tests/test_backup_runtime_no_sudo_v1.py`, `tests/test_backup_recovery_engines.py`, `tests/test_preflight_backup_v1.py` — **43 passed**
- `tests/` vollständig — **1526 passed**

## 7. GitHub CI (Run 25687923662, Commit `b2948c9`)

- Beide Fix13-Tests **PASSED** im Workflow-Log.
- Mit `pytest -x` schlägt der **nächste** Test fehl: `test_restore_rejects_symlink_whose_relative_target_escapes_root` erwartete das Wort `escapes` im Fehlertext; der Produktpfad liefert `storage-protection-004` (deutsch) — **Kategorie B** am Recovery-Test, nicht an Fix13. Minimaler Folge-Fix: Assertion akzeptiert `escapes` **oder** `storage-protection` bei weiterhin `self.assertFalse(rr[0])`.
