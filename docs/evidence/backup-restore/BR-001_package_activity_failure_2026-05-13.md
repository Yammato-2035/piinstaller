# BR-001 — Paketaktivität während Backup (STRICT Evidence, 2026-05-13)

**Job-ID:** `e341a326ac69`  
**Ziel (allein freigegeben):** `/media/gabriel/setuphelfer-back`  
**Ergebnis:** Abbruch mit **`backup.blocked_package_activity`**, **`diagnosis_id`:** **`UPDATE-CONFLICT-041`**, **`abort_reason`:** **`package_activity_detected_runtime`**.

**Regeln dieses Dokuments:** kein neuer Backup-Start, kein Verify, kein Restore, kein anderer Zielpfad. Keine produktiven Änderungen an Paket-Timern hier dokumentiert — nur Befund und Referenzen.

---

## Phase 1 — Job-Evidence

### `job.json` (Auszug, Pfad: `/var/lib/setuphelfer/backup-jobs/e341a326ac69/job.json`)

Vollständiger Inhalt (klein):

```json
{
  "job_id": "e341a326ac69",
  "backup_type": "full",
  "backup_dir": "/media/gabriel/setuphelfer-back",
  "source": "/",
  "lang": "",
  "requested_by": "api",
  "created_at": "2026-05-13T17:24:02.952234+00:00"
}
```

### `status.json` (Kernfelder, Pfad: `/var/lib/setuphelfer/backup-jobs/e341a326ac69/status.json`)

- **`status`:** `error`  
- **`code`:** `backup.blocked_package_activity`  
- **`diagnosis_id`:** `UPDATE-CONFLICT-041`  
- **`abort_reason`:** `package_activity_detected_runtime`  
- **`backup_started_at`:** `2026-05-13T17:24:03.027232+00:00`  
- **`backup_finished_at`:** `2026-05-13T19:07:39.802091+00:00`  
- **`archive_path`:** `/media/gabriel/setuphelfer-back/pi-backup-full-20260513_192403.tar.gz` (geplant; **kein finales Archiv** auf dem Medium)  
- **`partial_path`:** `…/pi-backup-full-20260513_192403.tar.gz.partial` — **`partial_deleted`:** **`true`**  
- **`manifest_tmp_path`:** `/media/gabriel/setuphelfer-back/.e341a326ac69.MANIFEST.json` (**Restdatei vorhanden**, siehe unten)  
- **`active_package_processes`:** ein Eintrag — **`apt-get`**, **`cmdline`:** `/usr/bin/apt-get autoremove --purge -y` (PID im Lauf: `34212`)  
- **`subprocess_returncode`:** `-15` (typisch für Abbruchsignal nach Policy)  
- **`tar_stderr_log`:** `/var/log/setuphelfer/backup-e341a326ac69.log` (nicht ins Repo kopiert)

### `systemctl status setuphelfer-backup@e341a326ac69.service` (Auszug, erfasst 2026-05-13)

- **Active:** `failed (Result: exit-code)`  
- **Hinweis:** Dauer ca. **1h 43min** (Deckung mit `backup_started_at` → `backup_finished_at`)

### `journalctl`

Im Evidence-Erfassungskontext: **`journalctl -u setuphelfer-backup@e341a326ac69.service`** lieferte **keine Zeilen** (Hinweis: Nutzer ggf. nicht in Gruppe **`adm`** / **`systemd-journal`**). Für vollständige Logs: auf dem Host **`sudo journalctl -u setuphelfer-backup@e341a326ac69.service`** verwenden.

### Manifest-Restdatei

Pfad: **`/media/gabriel/setuphelfer-back/.e341a326ac69.MANIFEST.json`**  
Inhalt (Stand Evidence): `job_id`, `backup_type`, `source`, `backup_dir`, `created_at`, leeres `completed_at`, Platzhalter `archive_size` / `hash`.

---

## Phase 2 — Paketaktivität / Timer

### Aktiver Paketprozess (aus `status.json`)

- **`/usr/bin/apt-get autoremove --purge -y`**

### Zeitlicher Zusammenhang (Mint-Update-Automation)

- **`mintupdate-automation-autoremove.timer`** / **`.service`:** Laut `systemctl list-timers` war der **letzte Lauf** nahe **`2026-05-13 21:07:39 CEST`**, was mit **`backup_finished_at`** (**`19:07:39Z`** = **21:07 MESZ**) zusammenfällt — **plausibler Kollision-Kontext** mit dem Backup-Abbruch.

### Relevante Timer (Snapshot `systemctl list-timers --all`, Auszug)

| Timer | ActiveState | UnitFileState | NextElapse (Beispiel aus Snapshot) |
|-------|-------------|---------------|-------------------------------------|
| `apt-daily.timer` | active | enabled | 2026-05-14 03:38:40 CEST |
| `apt-daily-upgrade.timer` | active | enabled | 2026-05-14 06:13:01 CEST |
| `mintupdate-automation-upgrade.timer` | active | enabled | 2026-05-14 00:30:52 CEST |
| `mintupdate-automation-autoremove.timer` | active | enabled | u. a. letzter Trigger nahe Abbruchzeit |
| `dpkg-db-backup.timer` | active | enabled | 2026-05-14 00:00:00 CEST |
| `apt-show-versions.timer` | active | enabled | 2026-05-14 00:00:00 CEST |

**Hinweis:** Timer **nicht dauerhaft deaktivieren** — für Retry nur **temporär** stoppen und nach dem Test wieder starten (siehe Runbook).

---

## Phase 3 — Sauberkeitsbefund (`find` maxdepth 1)

Befehl:

```bash
find /media/gabriel/setuphelfer-back -maxdepth 1 -type f \
  \( -name 'pi-backup-full-20260513_192403*' -o -name '.e341a326ac69*' -o -name '*.partial' -o -name '*.sha256' \) \
  -ls
```

**Ergebnis (Evidence-Lauf):**

- **`./.e341a326ac69.MANIFEST.json`** vorhanden (Rest-Manifest).  
- **Kein** Treffer für **`pi-backup-full-20260513_192403*.tar.gz`**.  
- **Keine** **`.partial`**-Datei für diesen Lauf.  
- **Keine** passende **`.sha256`** im Suchmuster.

**Abgleich mit Erwartung:** kein finales Archiv — keine `.partial` — Manifest-Restdatei **ja**.

---

## Verweise

- Maschinenlesbar: `BR-001.json` → **`br001_package_activity_failure_e341a326ac69_2026_05_13`**
- Sicherer Retry-Ablauf: **`BR-001_package_activity_retry_runbook_2026-05-13.md`**

---

## Follow-up (STRICT timer-pause Retry, 2026-05-13)

Geplanter erneuter Lauf **mit** temporärem Timer-Stopp scheiterte **vor** Timer-Stopp an **Phase 2** (laufende **`mintUpdate`** / **`unattended-upgrade-shutdown`**) und an fehlendem **`sudo`** im Agent für **`fuser`**/Timer-**stop**. Siehe **`BR-001_package_timer_paused_retry_2026-05-13.md`**.
