# BR-001 — Full-Backup-Lauf (STRICT, 2026-05-13)

**Ziel:** Erster echter Full-Backup-Test nur auf **`/media/gabriel/setuphelfer-back`**. **Kein** Restore, **kein** anderer Pfad, **kein** `/mnt/setuphelfer/backups`, **kein** `/media/setuphelfer/setuphelfer-back`.

## Phase 0 — Backend-Version-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-backend-version-gate.sh` | **Exit 0** — OK (HTTP 200, Versionsfelder, Config konsistent) |
| `GET http://127.0.0.1:8000/api/version` | **HTTP 200** — `project_version` **1.7.1**, `release_stage` **internal_testing** |
| `systemctl status setuphelfer-backend.service` | **active (running)** — Drop-Ins: `backup-target.conf`, `override.conf` |

## Phase 1 — Zielpfad direkt vor Start

| Prüfung | Ergebnis |
|---------|----------|
| `date -Is` (Start) | **2026-05-13T18:21:45+02:00** |
| `findmnt -T /media/gabriel/setuphelfer-back` | **TARGET** `/media/gabriel/setuphelfer-back`, **SOURCE** `/dev/sdb1`, **FSTYPE** **ext4**, **OPTIONS** **rw**,… |
| `/proc/mounts` | **rw** auf `/dev/sdb1` → `/media/gabriel/setuphelfer-back` |
| `lsblk` | **UUID** **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, **LABEL** **setuphelfer-back**, **MOUNTPOINTS** `/media/gabriel/setuphelfer-back`, **TRAN** usb — **nicht** Root-FS (`/` auf `nvme0n1p2`) |
| `systemctl show … ReadWritePaths` | enthält **`/media/gabriel/setuphelfer-back`** (u. a. `/opt/setuphelfer` … `/mnt/setuphelfer`) |
| `target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0` | **HTTP 200**, **`code":"backup.target_check_ok"`**, `mount_readonly": false`, Schreibtest ok |
| `date -Is` (Ende Phase 1) | **2026-05-13T18:21:45+02:00** |

**Abnahme Phase 1:** erfüllt (ext4, rw, UUID/Label, nur freigegebener Pfad, target-check ok).

## Phase 2 — Backup-Start (`POST /api/backup/create`)

Signatur laut Code: `backend/app.py` — `POST /api/backup/create`, JSON u. a. **`type`**, **`backup_dir`**, **`target`**, optional `async`, `sudo_password`, …

**Request (exakt):**

```json
{
  "type": "full",
  "backup_dir": "/media/gabriel/setuphelfer-back",
  "target": "local"
}
```

**Response (Auszug):**

- **HTTP 200**
- **`status":"error"`**
- **`code":"backup.starter_invalid_path"`**
- **`message`:** „Backup-Starter fehlgeschlagen“
- **`details`:** `diagnosis_id` **SYSTEMD-RUNNER-001**, `unit` **setuphelfer-backup@2ef832fc32a2.service**, `job_id` **2ef832fc32a2**

**Startzeit API:** `2026-05-13T16:22:02Z` (UTC) — Job sofort im Fehlerzustand (Starter lehnte Pfad ab).

## Phase 3 — Jobstatus

**`GET /api/backup/jobs/2ef832fc32a2`:**

| Feld | Wert |
|------|------|
| `status` | **error** |
| `code` | **backup.starter_invalid_path** |
| `started_at` | 2026-05-13T16:22:02.929211+00:00 |
| `finished_at` | 2026-05-13T16:22:02.955473+00:00 |
| `backup_dir` | `/media/gabriel/setuphelfer-back` |
| `backup_file` (geplant) | `/media/gabriel/setuphelfer-back/pi-backup-full-20260513_182202.tar.gz` |
| `partial_path` (geplant) | `…182202.tar.gz.partial` |
| `abort_reason` | **starter_failed** |

Kein paralleler zweiter Job.

## Ursache (Root Cause)

`/usr/lib/setuphelfer/setuphelfer-backup-starter` (**Polkit-/Privilege-Boundary**) erlaubte **`backup_dir`** bisher nur unter **`/mnt/setuphelfer/backups`**. Der freigegebene BR-001-Pfad **`/media/gabriel/setuphelfer-back`** war dort **nicht** in der Starter-Allowlist → **`backup.starter_invalid_path`**, obwohl API-`target-check` und Mount **rw** grün waren.

**Repo-Fix (nach diesem Lauf):** `packaging/helpers/setuphelfer-backup-starter.py` — **`ALLOWED_BACKUP_ROOTS`** erweitert um **`/media/gabriel/setuphelfer-back`** (exakt ein Eintrag, kein generisches `/media`). Tests: `packaging/helpers/tests/test_backup_starter_validation.py`.

**Operator:** aktualisierte Datei nach **`/usr/lib/setuphelfer/setuphelfer-backup-starter`** installieren (z. B. `sudo install -o root -g root -m 0755 …`) — im Agentenlauf **`sudo` nicht verfügbar** (TTY/Passwort), daher **kein** erneuter Live-Backup-Start möglich.

**Alternative (nur mit Betreiberfreigabe dokumentieren):** `Environment=SETUPHELFER_BACKUP_START_MODE=systemd` im Backend-Service, damit **`systemctl start`** ohne Helper-Pfadprüfung — ebenfalls **systemd-Override** und **Restart** nötig.

## Phase 4 — Artefakte

- Geplantes Archiv **`pi-backup-full-20260513_182202.tar.gz`** auf dem Medium: **nicht** angelegt (Job nie gestartet).
- **`.partial`:** für diesen Job **nein** (keine Datei mit diesem Präfix gefunden).
- **Manifest / SHA256:** nicht angelegt (kein erfolgreicher Lauf).

## Phase 5 / 6 — BR-004 / BR-005

**Nicht ausgeführt** — kein neues BR-001-Archiv aus diesem Lauf. Verify nur gegen **dieselbe** Datei wie BR-001 erlaubt.

## Phase 7 — Restore

**Nicht** gestartet (explizit verboten).

## Ergebnis

| Test | Status |
|------|--------|
| **BR-001** (dieser Full-Backup-Versuch) | **failed** / Gate-Kette **blocked** (Starter-Allowlist) |
| **BR-004** Verify Basic | **blocked** (kein neues Archiv) |
| **BR-005** Verify Deep | **blocked** (kein neues Archiv) |

## Referenzen

- `BR-001.json` → `br001_full_backup_attempt_2026_05_13`
- `packaging/helpers/setuphelfer-backup-starter.py` (Fix)
- `BR-001_systemd_readwritepaths_analysis_2026-05-13.md` (ReadWritePaths-Kontext)

## Nachtrag — Starter-Update und erneuter Versuch (2026-05-13, später)

Operator wollte den Repo-Starter nach **`/usr/lib/setuphelfer/setuphelfer-backup-starter`** installieren und BR-001 erneut starten. **Im Cursor-Agent:** **`sudo`** weiterhin **nicht** verfügbar (TTY/Passwort) → **kein** Install, **kein** zweites **`POST /api/backup/create`**. Vollständige Dokumentation: **`BR-001_starter_update_and_retry_2026-05-13.md`**, JSON-Key **`br001_starter_update_retry_2026_05_13`** in **`BR-001.json`**.

**Weiterer Nachtrag (Runner):** Job **`96ed5d89c443`** — **EROFS** auf Manifest (Runner-**`ProtectSystem=strict`**), **`status.json`** blieb **`queued`**, systemd **`failed`** → **`backup.job_conflict`** auf dem laufenden Backend bis Deploy von **`backend/app.py`** (stale-systemd-Sync). Siehe **`BR-001_runner_systemd_readwritepaths_fix_2026-05-13.md`**.

**Nachtrag STRICT stale-sync Retry:** Deploy nur **`app.py`** nach **`/opt`** + Backend-Restart — **`sudo`** Phase1 im Agent **blockiert** (TTY/Passwort); **`GET …/jobs/96ed5d89c443`** weiter **`queued`** + systemd **`failed`**; **`POST /api/backup/create`** weiter **`backup.job_conflict`**. Dokumentation: **`BR-001_stale_job_sync_fix_and_retry_2026-05-13.md`**.

**Nachtrag Paketaktivität (Job `e341a326ac69`):** Langer Full-Backup-Lauf auf **`/media/gabriel/setuphelfer-back`** abgebrochen mit **`backup.blocked_package_activity`** / **`UPDATE-CONFLICT-041`** (`apt-get autoremove --purge -y`, Mint-Timer). Partial entfernt, Manifest-Rest **`.e341a326ac69.MANIFEST.json`**. Evidence **`BR-001_package_activity_failure_2026-05-13.md`**, Retry-Runbook **`BR-001_package_activity_retry_runbook_2026-05-13.md`**.

**Nachtrag STRICT timer-pause Retry (ohne neuen Job):** Phase 0–1 grün; **Phase 2 STOP** wegen laufender **`mintUpdate`** / **`unattended-upgrade-shutdown`**; **`sudo`** für Locks und Timer-**stop** nicht verfügbar — **`POST /api/backup/create`** nicht ausgeführt. Evidence **`BR-001_package_timer_paused_retry_2026-05-13.md`**.

**Nachtrag Runner-Finalisierung (Job `2cff11287f67`, 2026-05-14):** Nach langem Tar-Lauf Hänger/Timeout in Hash+Manifest-Repack-Phase; Root Cause u. a. **dreifache** Finalisierung im Code + dritter SHA256-Scan — Evidence **`BR-001_runner_finalization_performance_failure_2026-05-14.md`**, Fix **`backend/tools/backup_runner.py`** (**BR-012**).

**Nachtrag Deploy-Prep (2026-05-14):** Version-Gate **OK**; **`sha256sum`** Workspace **`/home/volker/piinstaller/.../backup_runner.py`** = **`/opt/setuphelfer/.../backup_runner.py`** (**`77b5bbaa…`**); `finalize_*` in `/opt` vorhanden; **`sudo install`** im Agent nicht möglich (Passwort-TTY) — fachlich **kein** Byte-Wechsel nötig. **`GET /api/backup/jobs/2cff11287f67`** → **`error`**. Geplante Löschliste für alte **`.partial`**/**`.manifest-tmp`**/**`.2cff…MANIFEST.json`** am Ziel **nicht anwendbar** (Pfade fehlten); Sidecar **`.pi-backup-full-20260513_214230.tar.gz.partial.MANIFEST.json`** dokumentiert belassen. **`POST /api/backup/create`** in diesem Schritt **nicht**. JSON: **`br001_runner_fix_deploy_prep_2026_05_14`**.
