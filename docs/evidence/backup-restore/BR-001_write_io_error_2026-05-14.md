# BR-001 — Ziel-Schreib-E/A-Fehler (Job `f744c2936468`, STRICT Evidence, 2026-05-14)

**Ziel:** ausschließlich `/media/gabriel/setuphelfer-back`  
**Kein** neuer Backupstart, **kein** Verify, **kein** Restore in diesem Prompt.

---

## 1. Job- und Statusdaten

| Feld | Wert |
|------|------|
| **job_id** | `f744c2936468` |
| **backup_type** | `full` |
| **archive_path (geplant)** | `/media/gabriel/setuphelfer-back/pi-backup-full-20260514_083550.tar.gz` |
| **partial_path** | `/media/gabriel/setuphelfer-back/pi-backup-full-20260514_083550.tar.gz.partial` |
| **Partial-Größe (Snapshot)** | **67 779 952 640** Bytes (~63 GiB) — aus Betreiber-/Statuskontext |
| **status** | `error` |
| **code (Ist, zum Zeitpunkt Evidence)** | `backup.failed` |
| **diagnosis_id** | `null` |
| **abort_reason** | `tar_failed` |
| **subprocess_returncode** | `2` |
| **partial_deleted** | `false` |
| **backup_started_at** | `2026-05-14T06:35:50.743505+00:00` |
| **backup_finished_at** | `2026-05-14T07:25:11.786221+00:00` |
| **Laufzeit** | **~49 min** (systemd: **49 min 21 s**) |

### stderr-Kern (Auszug)

```
gzip: stdout: Input/output error
tar: /media/gabriel/setuphelfer-back/pi-backup-full-20260514_083550.tar.gz.partial: Wrote only 6144 of 10240 bytes
tar: Child returned status 1
tar: Error is not recoverable: exiting now
sh failed with exit status 2.
```

---

## 2. systemd

`setuphelfer-backup@f744c2936468.service`: **failed (Result: exit-code)**, Prozess **78670** beendet mit **status=1** (Runner), **Duration ~49 min**.

---

## 3. Ziel-Mount und Kapazität (Lesend)

| Prüfung | Ergebnis |
|---------|----------|
| `findmnt -T /media/gabriel/setuphelfer-back` | **SOURCE** `/dev/sdb1`, **FSTYPE** **ext4**, **OPTIONS** u. a. **`rw`**, **`errors=remount-ro`**, `stripe=8191` |
| `df -h` | **~22 %** belegt, ausreichend freier Platz (kein ENOSPC) |
| `lsblk` | `sdb` **1,8 T**, Partition **`sdb1`** → Zielpfad |

---

## 4. Kernel-Log (Lesend, eingeschränkt)

- **`journalctl -k` (09:15–09:35):** in dieser Umgebung **keine** Treffer (leer / keine Berechtigung für vollständigen Kernel-Ring).
- **`dmesg`:** **„Lesen des Kernelpuffers ist fehlgeschlagen“** (ohne erhöhte Rechte).

**Operator:** zum Absturzzeitpunkt (**~09:25 CEST**, Ende Job) lokal **`sudo dmesg -T`** bzw. **`sudo journalctl -k --since …`** nach **`I/O error`**, **`Buffer I/O error`**, **`sdb`**, **`ext4`**, **`USB`** auswerten.

---

## 5. Root-Cause-Klassifikation

| Kategorie | Bewertung |
|-----------|-----------|
| **Zielmedium / Blockschicht (EIO)** | **Primär** — `gzip: stdout: Input/output error` und **Short-Write** (`Wrote only …`) passen zu **EIO** auf dem **Schreibpfad** zur `.partial`. |
| **USB-/Transport / Strom** | **Wahrscheinlich mitbedingend** bei externen Platten — gesondert durch Hardware-Logs zu verifizieren. |
| **ext4 `errors=remount-ro`** | **Möglich** — nach ersten Schreibfehlern kann das FS **ro** remounten; weiteres Verhalten von Logs abhängig. |
| **Paketaktivität** | **Ausgeschlossen** (laut Auftrag). |
| **Runner-Finalisierung** | **Ausgeschlossen** — Abbruch **während** `tar|gzip`-Pipeline (`rc≠0`), vor Manifest/Hash. |
| **Produktcode-Logikfehler** | **Nicht** als Ursache der EIO; **Klassifikation** der Meldung im Runner war bis Fix **generisch** (`backup.failed`). |
| **systemd-Sandbox** | **Unwahrscheinlich** — Schreiben lief lange stabil; typisches Sandbox-Muster wäre sofortiger EACCES/EPERM, nicht EIO mitten im Lauf. |

---

## 6. Produkt-Follow-up (Repo)

- **BR-013:** `backup_runner.py` erkennt **`Input/output error`** und **`Wrote only … bytes`** in **tar/gzip-stderr** und setzt **`code`:** **`backup.write_io_error`**, **`diagnosis_id`:** **`BACKUP-IO-ERROR-050`**, **`abort_reason`:** **`target_write_io_error`**, **`partial_deleted`:** **`false`** (kein erzwungenes Löschen auf krankem Medium). i18n: **`backup.messages.write_io_error`** (DE/EN), Backend-Katalog **`K_TARGET_WRITE_IO_ERROR`**.
- **BR-004 / BR-005:** keine Verify-Kette auf **dieser** `.partial` / kein erfolgreiches BR-001-Archiv.

**Hinweis:** Der gesicherte **`status.json`**-Snapshot dieses Laufs zeigt noch **`backup.failed`** / **`tar_failed`** (vor Deploy des aktualisierten Runners auf den Host).

---

## 7. Verweise

- `BR-001.json` → **`br001_write_io_error_f744c2936468_2026_05_14`**
- KB: `docs/knowledge-base/backup/BACKUP_TARGET_WRITE_IO_ERROR.md`
