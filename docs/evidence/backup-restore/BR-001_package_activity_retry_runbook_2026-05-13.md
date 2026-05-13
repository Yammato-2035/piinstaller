# BR-001 — Retry nach `backup.blocked_package_activity` (Runbook, 2026-05-13)

**Kontext:** Job **`e341a326ac69`** ist mit **`UPDATE-CONFLICT-041`** / **`package_activity_detected_runtime`** fehlgeschlagen, u. a. wegen laufendem **`apt-get autoremove --purge -y`** (Mint-Update-Automation). Evidence: **`BR-001_package_activity_failure_2026-05-13.md`**.

**Zielpfad (unverändert):** nur **`/media/gabriel/setuphelfer-back`**.

**Hinweis (2026-05-13):** Ein automatisierter „Timer-pause“-Retry kann bereits an **Phase 2** scheitern, wenn weiterhin **`mintUpdate`** oder **`unattended-upgrade-shutdown`** läuft — dann zuerst Prozesse beenden/abwarten, **danach** erneut Phase 2 und erst bei sauberem Befund Timer stoppen. Evidence: **`BR-001_package_timer_paused_retry_2026-05-13.md`**.

**Verbote:** kein Restore, kein Verify vor finalem Archiv, kein anderer Backup-Pfad, **keine dauerhafte Deaktivierung** von APT-/Mint-Timern (nur **temporär** für die geplante Backup-Fenster).

---

## 1. Backend-Version-Gate

```bash
cd /home/volker/piinstaller
./scripts/check-backend-version-gate.sh
curl -sS -i http://127.0.0.1:8000/api/version | head -20
```

**Pflicht:** Skript **Exit 0**, **`/api/version`** **HTTP 200**.

---

## 2. Target-Check

```bash
curl -sS "http://127.0.0.1:8000/api/backup/target-check?backup_dir=/media/gabriel/setuphelfer-back&create=0" | jq .
```

**Pflicht:** **`code":"backup.target_check_ok"`**, **`mount.mount_readonly": false`**, **`write_test.success": true`**.

---

## 3. Paketprozesse prüfen

```bash
ps aux | grep -E '[a]pt|[d]pkg' || true
```

Erwartung vor Backup-Start: **keine** laufenden **`apt-get`**, **`dpkg`**, **`unattended-upgr`** (außer kurze Fenster — bei Zweifel warten oder Retry verschieben).

---

## 4. dpkg-/APT-Locks prüfen

```bash
sudo lsof /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock 2>/dev/null || true
ls -la /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock 2>/dev/null || true
```

Locks dürfen **nicht** von einem fremden Prozess gehalten werden, solange das Backup starten soll.

---

## 5. `dpkg --audit`

```bash
sudo dpkg --audit
```

Broken packages beheben (nach Distributions-Doku); sonst riskiert ein Backup erneuten Abbruch oder inkonsistente Systemzustände.

---

## 6. Timer temporär stoppen (nur Testfenster)

**Nur mit klarem Zeitfenster** (z. B. unmittelbar vor **`POST /api/backup/create`**) und **ohne** `disable`:

```bash
# Beispiel — nur ausführen, wenn Operator das Fenster bewusst wählt:
sudo systemctl stop apt-daily.timer
sudo systemctl stop apt-daily-upgrade.timer
sudo systemctl stop mintupdate-automation-upgrade.timer
sudo systemctl stop mintupdate-automation-autoremove.timer
sudo systemctl stop dpkg-db-backup.timer
sudo systemctl stop apt-show-versions.timer
```

**Hinweis:** `stop` auf **`.timer`** stoppt den Timer und unterbindet den **nächsten** geplanten Start bis **`start`** wieder erfolgt — **kein** `disable`, damit die Standardkonfiguration erhalten bleibt.

---

## 7. Timer wiederherstellen (unmittelbar nach Backup-Fenster)

```bash
sudo systemctl start apt-daily.timer
sudo systemctl start apt-daily-upgrade.timer
sudo systemctl start mintupdate-automation-upgrade.timer
sudo systemctl start mintupdate-automation-autoremove.timer
sudo systemctl start dpkg-db-backup.timer
sudo systemctl start apt-show-versions.timer
```

Kontrolle:

```bash
systemctl list-timers --all | grep -E 'apt-daily|mintupdate|dpkg-db|apt-show-versions'
```

---

## 8. Erst danach neuer BR-001-Start

- **`POST /api/backup/create`** mit **`backup_dir":"/media/gabriel/setuphelfer-back"`** — **neue** `job_id` ( **`e341a326ac69` nicht wiederverwenden** ).
- Kein paralleler zweiter Create.
- Optional: altes Rest-Manifest **`.e341a326ac69.MANIFEST.json`** vorher umbenennen/archivieren (Betreiberentscheidung; nicht automatisch löschen).

---

## 9. BR-004 / BR-005

**Nur** wenn BR-001 ein **finales** **`.tar.gz`** geliefert hat — **dieselbe** Archivdatei für Basic und Deep Verify laut Matrix.

---

## 10. Kein Restore

Kein Restore, kein Restore-Preview, kein `dd`/`mkfs` am Zielsystem.

---

## Referenzen

- `docs/evidence/backup-restore/BR-001_package_activity_failure_2026-05-13.md`
- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
