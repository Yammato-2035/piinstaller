# BR-001 — Produktives Backend: Workspace-Sync, `version.json`, Checks (2026-05-13)

**Modus:** STRICT — kein Backup-Start, kein Restore, kein anderer Zielpfad als `/media/gabriel/setuphelfer-back` für API-Checks, keine Mount-/Format-/Reparatur-Operationen.

## Phase 0 — Grenzen

Eingehalten: kein Backup, kein Restore, kein `/mnt/setuphelfer/backups`, kein `/media/setuphelfer/setuphelfer-back`, kein Bind, keine Pfadumdeutung, kein `dd`/`mkfs`, keine Datenlöschung.

## Phase 1 — Workspace / Git

| Feld | Wert |
|------|------|
| `git rev-parse HEAD` | `6398f1217d1d5b23e35f0a0d23bc16915d3aa7a4` |
| Arbeitsbaum | **nicht sauber** — sehr viele `M …` Einträge (gesamtes Repo lokal geändert) |
| `git log -1 --oneline` | `6398f12 docs: record backend diagnostic deploy target-check` |

**Hinweis:** Trotz dirty Tree wurden für den Abgleich **konkrete Pfade** unter `/home/volker/piinstaller/…` gelesen; kein blindes Massenkopieren aus unstaged Bereichen außerhalb der freigegebenen Deploy-Liste.

## Phase 2 — Produktiver Dienst

| Prüfung | Ergebnis |
|---------|----------|
| `systemctl status setuphelfer-backend.service` | **active (running)** |
| User / Group / WorkingDirectory | `setuphelfer` / `setuphelfer` / `/opt/setuphelfer` |
| Start | über `/opt/setuphelfer/scripts/start-backend.sh` → `uvicorn app:app` Port **8000** |
| `curl -i http://127.0.0.1:8000/api/version` | **HTTP 500** `Internal Server Error` |

## Phase 3 — Versioning / `version.json`

### `/opt/setuphelfer/config/version.json` (produktiv, **alt**)

```json
{
  "version": "1.5.0.0",
  "codename": "Deterministic Restore",
  "release_date": "2026-04-22"
}
```

- **Kein** `version_source_of_truth`, **kein** `project_version` im neuen Sinne → **`core.versioning.load_project_version()`** schlägt mit **`ValueError`** fehl → **`/api/version`** → **500**.

### Workspace `config/version.json` (**neu**)

- Enthält **`version_source_of_truth": true`**, **`project_version`**, **`release_stage`**, **`version_track`** (Schema laut `backend/core/versioning.py`).

### `core/versioning.py`

| Ort | SHA256 |
|-----|--------|
| Workspace | `39c22a547578ec5027455ef29565d6e8a368348a71cd2101999507d5544d0f1d` |
| `/opt/.../core/versioning.py` | **identisch** |

### Backend-Dateien vs. Workspace (SHA256, 2026-05-13)

| Datei | Workspace = `/opt`? |
|-------|----------------------|
| `backend/app.py` | **ja** (`60517c0c…`) |
| `backend/core/safe_device.py` | **ja** (`e33be50f…`) |
| `backend/core/versioning.py` | **ja** (`39c22a54…`) |
| `backend/core/diagnostics/registry.py` | **ja** (`5986134c…`) |
| `backend/core/diagnostics/matcher.py` | **ja** (`348335c2…`) |
| **`config/version.json`** | **nein** — Workspace `67a28e1f…`, `/opt` `23af5e3a…` |

**Kern:** Produktives **`/api/version`-Problem** ist hier primär **`/opt/setuphelfer/config/version.json`** (Schema), nicht fehlende Python-Module.

## Phase 4–6 — Backup unter `/tmp`, Install, Restart

**Status:** **BLOCKED** — `sudo` verlangt TTY/Passwort (`sudo: ein Terminal ist erforderlich …`).

- Geplantes Backup-Verzeichnis: **`/tmp/setuphelfer-deploy-backup-20260513T040623Z`** (nur Variable gesetzt; **`mkdir`/`cp` nicht ausgeführt** wegen sofortigem `sudo`-Fehler).
- **Keine** Änderung an `/opt` in diesem Agentenlauf.

**Operator:** Phasen 4–6 aus dem Master-Prompt interaktiv auf dem Host ausführen; mindestens **`config/version.json`** muss auf den Workspace-Stand (`sudo install … config/version.json`). Die fünf Backend-Dateien sind bereits byte-identisch zum Workspace — dennoch kann das Runbook alle sechs Dateien installieren, um Drift auszuschließen.

## Phase 7 — `/api/version` (Ist)

- **HTTP 500** (bis `version.json` auf neuem Schema liegt und Dienst neu lädt).

## Phase 8 — Freigabepfad (nur lesend)

| Kriterium | Erfüllt? |
|-----------|----------|
| Mountpoint | **`/media/gabriel/setuphelfer-back`** |
| UUID | **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`** |
| LABEL | **setuphelfer-back** |
| FS | **ext4** |
| `findmnt` OPTIONS | **`rw`,…** (Kernel/udisks2-Auszug) |
| Root-FS / nvme als SOURCE | **Nein** (`/dev/sdd1`) |
| TRAN usb | **Ja** (`usb`) |
| NTFS/exfat als Ziel | **Nein** (Ziel ext4) |

**Hinweis:** Aktuelles Blockgerät war **`/dev/sdd1`** (kann wechseln; maßgeblich UUID/Label/Mount).

## Phase 9 — `target-check` (nur Freigabepfad)

**Request:** `GET /api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`

- **HTTP 200**, JSON **`status":"error"`**, **`code":"backup.backup_target_not_writable"`**
- **`write_test`:** fehlgeschlagen — **`[Errno 30] Read-only file system`**, **`reason_code":"mount_readonly"`**
- **`mount.options`** in der API-Antwort: **`ro,…`** und **`mount_readonly": true`**

**Widerspruch zu Phase 8:** Shell-**`findmnt -T …`** meldet **`rw`**, die API meldet **`ro`** + EROFS beim Schreibtest → siehe **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`**.

## Phase 10 — BR-001

- **Kein** Backup gestartet, **keine** BR-001-Ausführung.
- BR-001 bleibt **`blocked`**; höchstens **`ready_for_explicit_operator_approval`** nach separater Nutzerfreigabe — derzeit **nicht** erfüllt, weil **`/api/version`** nicht grün und **`target-check`** nicht erfolgreich.

## SHA256 — Referenz „workspace“ (Quelle für Install)

```
60517c0c9cbae832b94788e419f13f6c8872084c45e37cb0b62c1f3ea5db486a  backend/app.py
e33be50f750ce36631f3d3943bc90e3d60d72bfbf669e6ba375ee5468a52b849  backend/core/safe_device.py
39c22a547578ec5027455ef29565d6e8a368348a71cd2101999507d5544d0f1d  backend/core/versioning.py
5986134ca868c981692c93af24dc8bcf1e5231014fc4b26986f0a5951adbc0a6  backend/core/diagnostics/registry.py
348335c22c4e9b299ff7fff0736845a3ad8395596be04627e3dd12be2547c0fe  backend/core/diagnostics/matcher.py
67a28e1f0e195a17bf07712c447402a73ed59e32dee12559fda9e0b67a722515  config/version.json
```

**SHA256SUMS.before / after / workspace** (vollständige Spalten): **nicht erzeugt** — Phase 4 nicht durchführbar ohne `sudo`.

## Gate-Skript `/api/version`-Parsing (2026-05-13)

- **Problem:** Produktiv lieferte **`GET /api/version`** teils **HTTP 200** mit **nur** `project_version`, `release_stage`, `version_track` (**ohne** `status":"success"`). Das Gate-Skript verlangte zwingend `status` → fälschlich Exit **16**.
- **Fix:** `scripts/check-backend-version-gate.sh` prüft **HTTP 200** und nicht-leere Pflichtfelder; **`status`** ist optional — wenn gesetzt, muss es **`success`** sein. Zusätzlich: Syntaxfehler in **`json_field()`** (ein Klammerzeichen zu viel) behoben; fehlerhafte **zweite** Zeile `"$tmp_body"` nach Heredoc entfernt (verursachte „Keine Berechtigung“ beim Ausführen der Temp-Datei).
- **Verifikation:** `./scripts/check-backend-version-gate.sh` → **Exit 0** (sofern Workspace- und `/opt`-`version.json` konsistent).

## Phase 12 — Tests

Nur Evidence/Doku im Repo geändert; **keine** zusätzliche Pytest-Pflicht für diesen Commit.

## Artefakte

- Diese Datei
- Aktualisierte `BR-001.json`, `BR-001_backend_deploy_status_2026-05-12.md`, `BR-001_productive_target_check_media_path_analysis_2026-05-12.md`, Release-Gates, `STATUS_MATRIX.md`, `docs/evidence/README.md`
- **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`**
