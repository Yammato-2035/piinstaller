# BR-001 — Runner-Finalisierung: Performance-/Hänger-Fehler (STRICT Evidence, 2026-05-14)

**Job-ID:** `2cff11287f67`  
**Ziel:** `/media/gabriel/setuphelfer-back` (einziger freigegebener Pfad)  
**Kein** Restore, **kein** Verify in diesem Vorfall.

---

## 1. Ausgangslage (Betrieb)

| Quelle | Befund |
|--------|--------|
| **`status.json`** (Snapshot) | `status`: **`running`**, `code`: **`backup.job.running`**, `backup_finished_at`: **null**, `progress_optional.bytes_current` ≈ **226114666496**, `running_for_s` ≈ **14357** (~4 h nach Start-Tar-Ende möglich) |
| **`systemctl status setuphelfer-backup@2cff11287f67.service`** | **failed (Result: timeout)**, Dauer **~10h 32min**, Prozess **SIGKILL** (TimeoutPolicy), **CPU** sehr hoch (Repack/Hash) |
| **Partial** | `/media/gabriel/setuphelfer-back/pi-backup-full-20260513_214230.tar.gz.partial` — Größe **226121290508** Bytes (~**210 GiB**) |
| **`.partial.manifest-tmp`** | **0 Byte** — leeres Ziel während `tarfile.open(..., "w:gz")` den neuen Stream aufbaut, bevor der erste Member geschrieben wird; bei **sehr langsamem** Repack stundenlang sichtbar |
| **Finales `.tar.gz`** | **nicht** vorhanden |
| **`tar` / `gzip`** | nach Ende der Archivphase **nicht** mehr aktiv; nur noch **`backup_runner.py`** (Python) |

### fd 3 / fd 4 (Beobachtung laut Operator)

- **fd 3:** Lesen der **`.partial`** (Python `tarfile` Lesezugriff für Hash und/oder Manifest-Rewrite).  
- **fd 4:** Ziel **`.partial.manifest-tmp`** — bleibt **0 Byte**, solange der **Schreib-`tarfile`** noch keinen komprimierten Block ausgegeben hat bzw. der Vorgang extrem langsam ist.  
- Leserate im Bereich **~1–1,5 MB/s** → bei **~210 GiB** nur **Lesen** für einen vollen Pass **O(10⁵ s)** Stunden; **dreifache** Passe im fehlerhaften Codepfad multipliziert das.

### RAM

Laut Operator: **RSS** bis **~15 GB** möglich (Tarfile-Buffer/Iterator), später **~6 GB** — typisch für große Member-Streams, nicht „alles in RAM“, aber hoch.

---

## 2. Codepfad-Analyse (`backend/tools/backup_runner.py`)

### 2.1 Wo wird `.partial` nach `tar` erneut gelesen?

1. **`_sha256_archive_payload(partial_path)`** — öffnet das Archiv mit **`tarfile.open(..., "r:*")`** und streamt **jeden** Member (ohne `MANIFEST.json`) für den deterministischen Payload-Hash. **Voller** Lesedurchlauf über die **komprimierte** Archivgröße.

2. **`_rewrite_manifest_in_archive(partial_path, …)`** — öffnet **`r:gz`** auf der **`.partial`**, schreibt parallel **`w:gz`** nach **`.partial.manifest-tmp`**: **vollständiger** Kopier-Repack (Manifest als erster Member, dann alle bisherigen Member). **Zweiter** Volldurchlauf Lesen + Schreiben.

3. **Vor Fix (Regression):** Nach `os.replace(partial_path, archive_path)` wurde **`_sha256_archive_payload(archive_path)`** **nochmals** für `manifest_hash` im Status aufgerufen — **dritter** Volldurchlauf.

### 2.2 Warum `.partial.manifest-tmp` 0 Byte lange?

`tmp = path.with_suffix(path.suffix + ".manifest-tmp")` → bei `…tar.gz.partial` wird **`…tar.gz.partial.manifest-tmp`**. Die Datei wird angelegt; erst wenn der **gzip**-Encoder ausreichend Daten puffert/ausgibt, steigt die Größe sichtbar — bei extrem langsamer Pipeline kann das lange **0 Byte** bleiben.

### 2.3 Kritischer Bug: dreifache Finalisierung

Im Erfolgszweig (`rc == 0`) umschloss **`for _ in range(3):`** **sowohl** SHA256 **als auch** Manifest-Rewrite. Bei **erfolgreichem** ersten Durchlauf liefen **dennoch zwei weitere** vollständige Hash+Rewrite-Zyklen — **Faktor ~3** auf Laufzeit und I/O.

### 2.4 Status während Finalisierung

Bisher wurde `progress_optional` in der **Tar-Monitor-Schleife** aktualisiert, **nicht** während Hash/Rewrite → UI/API wirkten „eingefroren“, obwohl CPU und fd aktiv waren.

### 2.5 Timeout / Stall

**systemd**-Unit-Timeout kann den Runner **SIGKILL**en — hinterlässt **`.partial`**. Dedizierte **Stall-Erkennung** im Runner (unveränderte Bytes/`mtime`) ist **Design-Bestandteil BR-012**, optional nachzurüsten.

---

## 3. Repo-Fix (Umsetzung 2026-05-14)

| Änderung | Zweck |
|----------|--------|
| **Nur einmal** `_sha256_archive_payload` vor Manifest-Embed | Entfernt **2×** redundante Full-Scans im Happy Path |
| **Höchstens 3×** nur **`_rewrite_manifest_in_archive`** bei Fehlversuch | Retries nur bei transientem Manifest-Fehler |
| **`manifest_hash`** im Erfolgs-`status` aus bereits berechnetem **`payload_hash`** | **Kein** dritter Full-Scan nach Rename |
| **`_throttled_finalize_progress`** + `finalize_phase` / `finalize_bytes_processed` in `progress_optional` | Sichtbarkeit während **finalizing_hash** / **finalizing_manifest** / **renaming** / **complete** |

**Keine** Abschwächung von Paketaktivitäts- oder Zielpfad-Logik.

---

## 4. Tests

- `backend/tests/test_backup_runner_finalization_v1.py` — Throttle-Verhalten, Progress bei großem Member, Hash-Invariante nach Manifest-Embed.

---

## 5. Verweise

- `BR-001.json` → **`br001_runner_finalization_performance_2cff11287f67_2026_05_14`**
- Testmatrix: **BR-012**
- Code: `backend/tools/backup_runner.py`

---

## 6. Produktiv-Deploy / Retry-Vorbereitung (2026-05-14, STRICT)

| Prüfung | Ergebnis |
|---------|----------|
| Workspace-`git` HEAD | **`e0a2e28`** — `fix: improve backup runner finalization performance` |
| `./scripts/check-backend-version-gate.sh` | **Exit 0** |
| `GET /api/version` | **HTTP 200** — `project_version` **1.7.1**, `backend_runtime_path` **`/opt/setuphelfer/backend`** |
| `sha256sum` Workspace vs. `/opt/.../backup_runner.py` | **identisch** — **`77b5bbaa1f84f4138d7632f9184200e6675b760a2bbbca3211dcea03825dd6d4`** |
| `grep finalize_phase` auf `/opt/.../backup_runner.py` | Treffer vorhanden (`finalize_phase` / `finalize_bytes_processed`) |
| `sudo install …` laut Runbook | In diesem Agent-Lauf **nicht ausführbar** (`sudo: ein Terminal ist erforderlich …`); fachlich **kein zusätzlicher Byte-Wechsel** nötig, weil Opt bereits dem Fix-Commit entspricht |
| `GET /api/backup/jobs/2cff11287f67` | **`status":"error"`**, Meldung u. a. systemd-Runner fehlgeschlagen |
| `systemctl status setuphelfer-backup@2cff11287f67.service` | **failed (Result: timeout)**, **SIGKILL**, Dauer **~10h 32min** |
| `systemctl show setuphelfer-backup@2cff11287f67.service` (Auszug) | **`TimeoutStartUSec=1min 30s`**, **`TimeoutStopUSec=30s`**, **`RuntimeMaxUSec=infinity`**, **`WatchdogUSec=0`** |
| Finales Archiv `pi-backup-full-20260513_214230.tar.gz` | **fehlt** weiterhin |
| Geplante Cleanup-Pfade (`…214230…partial`, `…manifest-tmp`, `.2cff11287f67.MANIFEST.json`) | **nicht vorhanden** zum Prüfzeitpunkt — **kein** `rm` ausgeführt (nichts zu löschen bzw. Operator hat Partial bereits entfernt) |
| Verbleibendes Sidecar | **`.pi-backup-full-20260513_214230.tar.gz.partial.MANIFEST.json`** (**348** Byte) — **nicht** gelöscht (Dokumentations-/Spurenartefakt; nicht in der expliziten Dreier-Löschliste) |
| Paralleles Zielmedium (Hinweis) | **`pi-backup-full-20260514_083550.tar.gz.partial`** — **kein** Teil dieses Prompts; **kein** Verify, **kein** Umbenennen; nächster BR-001-Retry erst nach **grünen Gates** und klarer Job-Disziplin |

**Kein** `POST /api/backup/create` in diesem Lauf.
