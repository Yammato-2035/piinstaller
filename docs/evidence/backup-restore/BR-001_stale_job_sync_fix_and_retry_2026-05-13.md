# BR-001 — Stale-Job-Sync (`app.py`) Deploy-Versuch und Retry (STRICT, 2026-05-13)

**Ziel:** Produktives **`/opt/setuphelfer/backend/app.py`** mit Workspace-Stand (enthält **`_sync_stale_runner_job_from_systemd`**, Anpassungen **`_has_active_long_running_job`**, **`backup_jobs_list`**, **`backup_job_status`**) ausrollen, Backend neu starten, alten Job **`96ed5d89c443`** per API anstoßen (Sync), **`backup.job_conflict`** beseitigen, neuen Full-Backup-Job starten, bei Erfolg **BR-004**/**BR-005** mit demselben Archiv. **Kein** Restore, **kein** anderer Zielpfad als **`/media/gabriel/setuphelfer-back`**.

## Ergebnis (Abnahme)

**BLOCKED** — **Phase 1** (`sudo mkdir` für `/tmp/setuphelfer-app-sync-fix-backup-*`) scheiterte:  
`sudo: ein Terminal ist erforderlich, um das Passwort zu lesen` / `Ein Passwort ist notwendig`.  
Damit: **kein** Backup von **`/opt/.../app.py`**, **kein** `install` nach `/opt`, **kein** `systemctl restart setuphelfer-backend.service`, **kein** produktiver Fix aktiv.

## Phase 0 — Workspace / Git

| Prüfung | Ergebnis |
|---------|----------|
| `git rev-parse HEAD` | **`0c874c5b868175f75b3c4acc2b7cf5d28203f5ce`** |
| `git log -1 --oneline` | **`0c874c5` docs: record BR-001 runner readwritepaths retry evidence** |
| `grep -n "_sync_stale_runner_job_from_systemd" backend/app.py` | **Treffer vorhanden** (Fix im Repo-Workspace) |
| `grep -n "_has_active_long_running_job" backend/app.py` | **Treffer vorhanden** |

## SHA256 `app.py` (vor Deploy — Ist-Zustand)

| Ort | SHA256 |
|-----|--------|
| Workspace **`/home/volker/piinstaller/backend/app.py`** (HEAD) | **`d3b9d85c91ebebe906e7938a64d9d9f4bcffea9840156b84915146568f06d668`** |
| Produktiv **`/opt/setuphelfer/backend/app.py`** | **`60517c0c9cbae832b94788e419f13f6c8872084c45e37cb0b62c1f3ea5db486a`** |

**Hinweis:** Unterschiedliche Hashes bestätigen: **Stale-Sync-Logik ist auf dem Host noch nicht aktiv** (Deploy ausstehend).

## Phase 1–3 — Geplant / nicht ausgeführt

- **`$BACKUP`** unter `/tmp/…`: nicht angelegt (sudo).
- **`sudo install … app.py`**: nicht ausgeführt.
- **`sudo systemctl restart setuphelfer-backend.service`**: nicht ausgeführt.

## Lesende Verifikation (ohne Deploy)

### Backend-Version-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-backend-version-gate.sh` | **Exit 0** (OK) |

### Alter Job `96ed5d89c443` — `GET /api/backup/jobs/96ed5d89c443`

- API liefert weiterhin **`"status": "queued"`** im Job-Objekt, eingebettetes **`systemd`**: **`ActiveState": "failed"`**, **`Result": "exit-code"`** — typisch für **altes** Backend ohne RAM-Sync auf **failed**.
- **`POST /api/backup/create`** mit  
  `{"type":"full","backup_dir":"/media/gabriel/setuphelfer-back","target":"local"}`  
  → **`code":"backup.job_conflict"`** — **Konflikt nicht beseitigt** (Deploy fehlt).

### Target-Check (Vorbedingung laut Runbook)

- **`GET …/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0`**
  - **`code":"backup.target_check_ok"`**
  - **`mount.mount_readonly": false`**, **`write_test.success": true`**
  - Mount: **`/dev/sdb1`**, **ext4**, **rw**, **`/media/gabriel/setuphelfer-back`**
  - **`lsblk`**: **UUID** **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, **LABEL** **setuphelfer-back**

### BR-004 / BR-005

**Nicht ausgeführt** — kein erfolgreiches neues BR-001-Archiv aus diesem Lauf.

### Restore

**Nicht gestartet.**

## Operator-Folgeschritt

Auf dem Host **interaktiv** (TTY) oder mit konfiguriertem **`sudo` ohne Passwort** für die betroffenen Befehle:

1. Phase 1–2 aus dem Master-Prompt (Backup von `/opt/.../app.py`, `install` Workspace → `/opt`, SHA256 prüfen).
2. `systemctl restart setuphelfer-backend.service`.
3. Gate + `GET …/jobs/96ed5d89c443` erneut; erwarten: Job nicht mehr blockierend **`queued`** bzw. **`backup.job_conflict`** weg.
4. Neues **`POST /api/backup/create`** → neue **`job_id`** (nicht **`96ed5d89c443`**).

## Verweise

- `BR-001.json` → Key **`br001_stale_job_sync_deploy_retry_attempt_2026_05_13`**
- Kontext Runner/EROFS: **`BR-001_runner_systemd_readwritepaths_fix_2026-05-13.md`**
