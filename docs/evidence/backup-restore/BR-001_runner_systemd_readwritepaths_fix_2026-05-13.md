# BR-001 — Runner-Unit `ReadWritePaths` und EROFS-Manifest (STRICT, 2026-05-13)

**Ziel:** Fehlerjob **`96ed5d89c443`** dokumentieren, Schreibzugriff der **Runner-Unit** `setuphelfer-backup@.service` auf **`/media/gabriel/setuphelfer-back`** sicherstellen, **BR-001** erneut starten (neue `job_id`), optional **BR-004/BR-005** auf dasselbe Archiv. **Kein** Restore.

## Freigabe (unverändert)

| Feld | Wert |
|------|------|
| Zielpfad | **`/media/gabriel/setuphelfer-back`** |
| Device | **`/dev/sdb1`** |
| UUID | **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`** |
| LABEL | **setuphelfer-back** |
| FS | **ext4**, **rw** |

---

## Phase 0 — Backend-Version-Gate (Agent)

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-backend-version-gate.sh` | **Exit 0** |
| `GET /api/version` | **HTTP 200** |
| `setuphelfer-backend.service` | **active (running)** |

---

## Phase 1 — Alter Job `96ed5d89c443`

### `systemctl status setuphelfer-backup@96ed5d89c443.service`

- **Active:** **failed (Result: exit-code)**  
- **Main PID:** beendet mit **status=1/FAILURE**  
- **Dauer:** sehr kurz (typisch für sofortigen Laufzeitfehler)

### `job.json` (lesbar ohne sudo)

Pfad: `/var/lib/setuphelfer/backup-jobs/96ed5d89c443/job.json`

- **`backup_dir`:** **`/media/gabriel/setuphelfer-back`** (korrekt, kein anderer Pfad)
- **`backup_type`:** **full**

### `status.json` (Stand Agent)

Enthält noch **`"status": "queued"`** — der Runner hat den Endzustand **nicht** nach `/var/lib/.../status.json` zurückgeschrieben (Abbruch vor Aktualisierung).

### Erwarteter Fehler (Betreiber / journalctl mit `adm` oder `sudo`)

Symptom laut Vorgabe: **`OSError: [Errno 30] Read-only file system`** beim Schreiben von  
**`/media/gabriel/setuphelfer-back/.96ed5d89c443.MANIFEST.json`** — **systemd-Sandbox** der Runner-Unit: **`ProtectSystem=strict`** ohne Schreibrecht auf das **USB-Ziel**.

### Artefakt-Suche (maxdepth 1)

Muster **`pi-backup-full-20260513_183443*`**, **`.96ed5d89c443*`**, **`*.partial`**: im Agent-Lauf **keine** Treffer (kein finales Archiv aus diesem Job).

### Verify

**BR-004 / BR-005:** nicht ausgeführt (kein finales Archiv).

---

## Phase 2 — Runner-Unit Ist-Zustand (`systemctl cat`)

**Hauptunit** (`/etc/systemd/system/setuphelfer-backup@.service`):

- **`ProtectSystem=strict`**
- **`PrivateTmp=yes`**
- **`ReadWritePaths=`** (vor Repo-Fix): **`/mnt/setuphelfer`** **`/var/lib/setuphelfer`** **`/var/log/setuphelfer`** — **ohne** **`/media/gabriel/setuphelfer-back`**

**Drop-In** (`/etc/systemd/system/setuphelfer-backup@.service.d/backup-target.conf`) auf dem Host (Agent):

```ini
[Service]
ReadWritePaths=/media/gabriel/setuphelfer-back
```

**Effektiv (`systemctl cat` / `show`):** systemd **merged** zu:

`ReadWritePaths=/mnt/setuphelfer /var/lib/setuphelfer /var/log/setuphelfer /media/gabriel/setuphelfer-back`

---

## Phase 3 — Repo-Anpassungen (Drop-In-Vorlage + Unit-Template)

1. **`packaging/systemd/setuphelfer-backup@.service`** — **`ReadWritePaths`** um **`/media/gabriel/setuphelfer-back`** ergänzt (Neuinstallationen konsistent).
2. **`docs/operations/systemd/setuphelfer-backup-at-service-backup-target.conf.example`** — Drop-In mit **vollständiger** Liste (leeres `ReadWritePaths=` + eine Zeile mit allen Pfaden), falls ein schmales Drop-In sonst Pfade „verliert“.

**Operator auf dem Host (falls nötig):** Drop-In wie in der Example-Datei setzen, **`daemon-reload`**.

**Hinweis:** Phase-3-**`sudo`**-Schritte (Backup unter `/tmp/...`, `tee` nach `/etc/systemd/...`) waren im **Agent nicht ausführbar** (Passwort/TTY); der Host zeigt bereits ein Drop-In mit Media-Pfad.

---

## Phase 4 — Prechecks vor neuem BR-001

- **`target-check`:** **`backup.target_check_ok`**, **`mount_readonly: false`**, Schreibtest ok  
- **`setuphelfer-backend` ReadWritePaths:** enthält **`/media/gabriel/setuphelfer-back`**  
- **`setuphelfer-backup@dummy` ReadWritePaths:** **`/mnt/setuphelfer /var/lib/setuphelfer /var/log/setuphelfer /media/gabriel/setuphelfer-back`**

---

## Phase 5–6 — Neuer BR-001-Job (Produktion zum Zeitpunkt Agent)

**`POST /api/backup/create`** mit  
`{"type":"full","backup_dir":"/media/gabriel/setuphelfer-back","target":"local"}`  
→ **`backup.job_conflict`** — Grund: **`BACKUP_JOBS`** im Backend-Prozess hielt **`96ed5d89c443`** weiterhin für **aktiv** (`status.json` noch **`queued`**, RAM nicht synchron mit **systemd failed**).

### Repo-Fix (Backend, Workspace)

In **`backend/app.py`**:

- **`_sync_stale_runner_job_from_systemd`**: Wenn **`status.json`** noch nicht-terminal ist, die **systemd-Unit** aber **`failed` / `exit-code`** meldet → RAM-Job auf **`error`** setzen (inkl. **`finished_at`**).
- **`_has_active_long_running_job`**: ruft diese Sync-Funktion für alle Jobs auf, bevor die Konfliktprüfung läuft.
- **`GET /api/backup/jobs`** / **`GET /api/backup/jobs/{id}`**: Sync vor Ausgabe; bei RAM-**`error`** wird **`_job_snapshot`** bevorzugt, falls die Datei noch **`queued`** meldet.

**Wirkung:** Nach **Deploy** dieser **`app.py`** nach **`/opt/setuphelfer/backend/`** und **`systemctl restart setuphelfer-backend.service`** sollte **`backup.job_conflict`** verschwinden; anschließend neues **`POST /api/backup/create`** → neue **`job_id`** (nicht **`96ed5d89c443`**).

---

## Phase 7–10 — Artefakte, BR-004/BR-005, kein Restore

Im Agent-Lauf: **kein** erfolgreicher neuer Job, daher **kein** finales **`.tar.gz`**, **kein** Verify, **kein** Restore.

---

## Nächste Schritte (Abnahme)

1. **`app.py`**-Änderung nach **`/opt/setuphelfer/backend/app.py`** deployen, Backend **neu starten**.  
2. **`GET /api/backup/jobs`** — **`96ed5d89c443`** sollte **nicht** mehr als laufend erscheinen (RAM **`error`**).  
3. **`POST /api/backup/create`** (gleicher JSON-Body) — neue **`job_id`** abwarten, Job pollen bis **`success`**.  
4. **`POST /api/backup/verify`** mit **`backup_file`** = Archivpfad, **`mode":"basic"`** dann **`mode":"deep"`**.

---

## Referenzen

- `BR-001.json` → `br001_runner_readwritepaths_and_stale_sync_2026_05_13`
- `packaging/systemd/setuphelfer-backup@.service`
- `docs/operations/systemd/setuphelfer-backup-at-service-backup-target.conf.example`

---

## Nachtrag — Paketaktivität (unabhängiger Abbruchpfad)

Ein späterer produktiver Lauf (**Job `e341a326ac69`**) scheiterte **nicht** an EROFS/ReadWritePaths, sondern an **`backup.blocked_package_activity`** (**`UPDATE-CONFLICT-041`**) durch laufendes **`apt-get autoremove`** im Mint-Automation-Kontext. Siehe **`BR-001_package_activity_failure_2026-05-13.md`** und **`BR-001_package_activity_retry_runbook_2026-05-13.md`**.

**Nachtrag Timer-pause Retry:** **`BR-001_package_timer_paused_retry_2026-05-13.md`** (STOP Phase 2 / sudo).
