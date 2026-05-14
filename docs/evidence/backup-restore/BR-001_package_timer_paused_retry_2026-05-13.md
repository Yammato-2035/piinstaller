# BR-001 — Retry mit temporär pausierten Paket-Timern (STRICT, 2026-05-13)

**Ziel:** Nach dokumentiertem Abbruch **Job `e341a326ac69`** (**`backup.blocked_package_activity`**) erneut **Full-Backup** nur auf **`/media/gabriel/setuphelfer-back`**, mit **temporärem** Stopp der Paket-**Timer** (ohne `disable`), danach **Timer wieder `start`**.

**Ergebnis dieses Laufs:** **STOP vor Phase 4** — Abbruchbedingung **Phase 2** erfüllt (**aktive Paket-/Mint-bezogene Prozesse**). Zusätzlich: **`sudo`** im Agent-Umfeld **nicht nutzbar** (TTY/Passwort) → **keine** `fuser`-Lock-Prüfung, **kein** `dpkg --audit`, **kein** `systemctl stop`/`start` der Timer durch diesen Lauf.

**Kein** `POST /api/backup/create` in diesem Prompt. **Kein** Restore, **kein** Verify.

---

## Phase 0 — Version und Runtime-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-backend-version-gate.sh` | **Exit 0** — OK |
| `GET /api/version` | **HTTP 200** — u. a. `project_version` **1.7.1**, `version_source_of_truth` **true** |
| `setuphelfer-backend.service` | **active (running)** |

**Abnahme Phase 0:** erfüllt.

---

## Phase 1 — Zielpfad

| Feld | Ist |
|------|-----|
| Zeit | `2026-05-13T21:20:39+02:00` (lokal) |
| `findmnt -T /media/gabriel/setuphelfer-back` | **TARGET** `/media/gabriel/setuphelfer-back`, **SOURCE** `/dev/sdb1`, **FSTYPE** **ext4**, **OPTIONS** **rw**,… |
| `/proc/mounts` | `/dev/sdb1` → Ziel, **rw** |
| `lsblk` | **UUID** **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, **LABEL** **setuphelfer-back**, **ext4** |
| `target-check?backup_dir=…&create=0` | **`code":"backup.target_check_ok"`**, **`mount_readonly": false`**, **`write_test.success": true** |

**Abnahme Phase 1:** erfüllt.

---

## Phase 2 — Paketprozesse / Locks

**`ps -ef | grep -Ei 'apt|dpkg|unattended|packagekit|mintupdate|update-manager'`** (Auszug, relevant):

- `root … /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal`
- `gabriel … mintUpdate`

**`sudo fuser …` / `sudo dpkg --audit`:** nicht ausführbar — `sudo: ein Terminal ist erforderlich …` / Passwort.

**Laufende Services (Auszug):** u. a. **`unattended-upgrades.service`** **active**.

**Regel im Prompt:** *Wenn aktive apt/dpkg/mintupdate-Prozesse oder Locks vorhanden: STOP, kein Backup.*

→ **STOP** (mindestens **MintUpdate**-Prozess und **unattended-upgrade-shutdown**; Locks wegen fehlendem `sudo` nicht verifizierbar).

---

## Phase 3 — Timer-Zustand (nur dokumentiert)

Auszug **`systemctl list-timers --all`** (gefiltert) und **`systemctl is-active`**:

- `apt-daily.timer`, `apt-daily-upgrade.timer`, `dpkg-db-backup.timer`, `apt-show-versions.timer`, `mintupdate-automation-upgrade.timer`, `mintupdate-automation-autoremove.timer`: überwiegend **active** (Timer-Einheiten).
- `unattended-upgrades.service`: **active**
- `packagekit.service`: **inactive** (im erfassten Moment)

Lokale Kopie der Ausgabe (nicht im Git): Host-Datei unter **`/tmp/setuphelfer-package-timers-20260513T192137Z.txt`** (nur zur Operator-Nachverfolgung).

---

## Phase 4–6 — Nicht ausgeführt

- **Phase 4** (Timer **stop**): erfordert **`sudo`** → nicht ausgeführt; wegen **Phase-2-STOP** ohnehin nicht sinnvoll fortgesetzt.
- **Phase 5** (`POST /api/backup/create`): **nicht** aufgerufen.
- **Phase 6** (Poll): entfällt.

---

## Phase 7–11 — Nicht ausgeführt

Kein finales Archiv, kein Verify, kein Restore.

---

## Phase 8 — Timer-Wiederherstellung

Kein vorheriges **`stop`** durch diesen Lauf → **`start`** der Paket-Timer hier **nicht** erforderlich. **Hinweis:** Hätte Phase 4 mit `sudo` stattgefunden, wäre Phase 8 zwingend mit **`systemctl start …timer`** nachzuziehen (siehe Runbook).

---

## Operator-Hinweise für einen erfolgreichen Retry

1. Sitzung mit funktionierendem **`sudo`** (TTY).
2. Phase 2 erfüllen: ggf. **MintUpdate** beenden bzw. in Ruhephase bringen; **unattended-upgrades**-Fenster abwarten oder nach Betreiberpolicy handeln — solange die **STRICT**-Zeile „keine aktiven Prozesse“ verlangt wird.
3. **`sudo fuser`** auf den dpkg/apt-Locks und **`sudo dpkg --audit`** ausführen.
4. Timer wie im Runbook **`BR-001_package_activity_retry_runbook_2026-05-13.md`** nur **`stop`**, nach Backup wieder **`start`**.
5. Dann **`POST /api/backup/create`** mit neuer **`job_id`**.

**Nacharbeit 2026-05-14:** Ein späterer Clean-Retry kann an **Runner-Finalisierung** (Hash/Manifest-Repack, systemd-Timeout) scheitern — Job **`2cff11287f67`**, Evidence **`BR-001_runner_finalization_performance_failure_2026-05-14.md`**, Code-Fix **`backup_runner.py`** (**BR-012**).

---

## Verweise

- Vorheriger Fehler: **`BR-001_package_activity_failure_2026-05-13.md`**
- Runbook: **`BR-001_package_activity_retry_runbook_2026-05-13.md`**
- Maschinenlesbar: `BR-001.json` → **`br001_package_timer_paused_retry_attempt_2026_05_13`**

**Bezug 2026-05-14:** Nach dem Runner-Finalisierungs-Fix (**`e0a2e28`**) bleibt der **timer-pause-Retry** unverändert relevant: **kein** neuer BR-001-Start, solange Phase 2 (Paket-/Mint-Prozesse) oder fehlendes **`sudo`** für temporären Timer-**stop** die STRICT-Regeln auslösen. Deploy-Prep und Medien-Inventar: **`BR-001_runner_finalization_performance_failure_2026-05-14.md`** Abschnitt 6, JSON **`br001_runner_fix_deploy_prep_2026_05_14`**.
