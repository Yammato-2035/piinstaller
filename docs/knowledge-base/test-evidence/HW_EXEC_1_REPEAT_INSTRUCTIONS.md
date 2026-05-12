# HW-EXEC-1-REPEAT — Anleitung (post FIX-1)

Diese Datei ist **git-tracked**; Evidence-JSON liegt unter `data/diagnostics/evidence/` (lokal, i. d. R. nicht im Commit).

## Vorbereitung (vor jedem Lauf)

1. **root:** `/mnt/setuphelfer/backups` existiert, `chown root:setuphelfer`, `chmod 0770` (Installer/postinst oder manuell konsistent).
2. **NVMe:** nur unter **`/mnt/setuphelfer/backups/<test-run>`** einhängen; **kein** `/media/<user>`. — Details: Abschnitt **Mount-Vorbereitung** unten.
3. **Dienst:** `systemctl daemon-reload && systemctl restart setuphelfer-backend`
4. **Vorab:** Schreibprobe als Dienstnutzer (Gruppe `setuphelfer`); `validate_write_target` darf keinen `STORAGE-PROTECTION-*` werfen.

---

## Mount-Vorbereitung (nach Dateisystem)

### ext4 (**empfohlen für HW1**)

1. Zielverzeichnis anlegen (falls noch nicht vorhanden):

   ```bash
   sudo mkdir -p /mnt/setuphelfer/backups/<test-run>
   ```

2. **Mount ohne** die Optionen `gid=` / `umask=` — diese gehören **nicht** zu ext4 und führen zu Mount-Fehlern (siehe Abschnitt *Typischer Fehler*).

   ```bash
   sudo mount /dev/<partition> /mnt/setuphelfer/backups/<test-run>
   ```

3. Rechte **nach** dem Mount setzen (native Linux-ACLs auf dem Dateisystem):

   ```bash
   sudo chown root:setuphelfer /mnt/setuphelfer/backups/<test-run>
   sudo chmod 0770 /mnt/setuphelfer/backups/<test-run>
   ```

**Begründung:** ext4 nutzt Unix-Besitzer/Gruppe/Modus. Gruppenzugriff für den Dienst erreicht man über **`chown`/`chmod`**, nicht über FUSE-typische Mount-Optionen.

---

### NTFS / exFAT (**für HW1 nicht empfohlen**)

- Für diese Typen können unter Linux oft Optionen wie **`uid=`**, **`gid=`**, **`umask=`** (bzw. ntfs-3g-Äquivalente) genutzt werden — das Verhalten weicht aber von ext4 ab, Rechte sind **nicht** gleichwertig, und Verify/Diagnose können **anders** aussehen als auf ext4.
- **HW1-Tests:** Partition möglichst als **ext4** vorbereiten und wie oben mounten.
- *Nur zur Dokumentation* (nicht für HW1 empfohlen), Beispiel NTFS mit ntfs-3g:

  ```text
  sudo mount -t ntfs-3g -o gid=setuphelfer,umask=007 /dev/<partition> /mnt/setuphelfer/backups/<test-run>
  ```

  exFAT: Distributionsspezifisch (`uid=`, `gid=`, `umask=`); vor Gebrauch `man mount.exfat` / Handbuch prüfen.

---

## Typischer Fehler (ext4 + falsche Optionen)

**Meldung (Beispiel):**  
`mount: … Falscher Dateisystemtyp, ungültige Optionen …` / `wrong fs type, bad option …`

**Ursache:**  
Bei **ext4** wurden Optionen wie **`gid=setuphelfer,umask=007`** an `mount` übergeben. Das sind **keine** gültigen ext4-Mount-Optionen im üblichen Sinne; der Kernel lehnt den Aufruf ab oder meldet einen ungültigen Optionssatz.

**Lösung:**  
`umount` (falls teilweise gemountet), dann **ohne** diese Optionen mounten und wie unter *ext4* **`chown root:setuphelfer`** + **`chmod 0770`** auf dem Einhängepunkt ausführen.

---

## Reihenfolge

HW1-01 → HW1-02 → HW1-03 → HW1-04 → HW1-05 (nicht mischen, Zielpfad während Serie nicht wechseln).

## EvidenceRecord pro Test (Pflicht)

Nach jedem Schritt eine neue Datei `data/diagnostics/evidence/EVID-2026-HW1-R<NN>.json` (eindeutige ID), z. B.:

```bash
cd /path/to/piinstaller
backend/.venv/bin/python scripts/diagnostics/new_evidence_record.py \
  --id EVID-2026-HW1-R01 \
  --scenario HW1-01 \
  --outcome failed \
  --profile profile-linux-laptop-nvme-host
```

Anschließend JSON **manuell** ergänzen: `test_goal`, `storage_profile`, `observed_symptoms`, `raw_signals` (API-`code`/`severity`, relevante Logzeilen), `matched_diagnosis_ids`, `suspected_root_causes`, `confirmed_root_cause` (nur bei belastbarer Evidenz).

## SUCCESS (streng)

Nur `outcome: success`, wenn Backup **und** Verify **und** Preview **und** Post-Checks (API+UI) grün sind **und** im dokumentierten Pfad **kein** sudo für Tar/Verify/Preview genutzt wurde **und** keine verbotenen Workarounds (777, `/media`, …).

## Matrix aktualisieren

In `data/diagnostics/hw_test_1_matrix.json` je Zeile HW1-01..05:

- `hw_exec_1_repeat_post_fix1.status` → `passed` | `failed` | `inconclusive` | `blocked`
- `hw_exec_1_repeat_post_fix1.evidence_id` → z. B. `EVID-2026-HW1-R01`
- `hw_exec_1_repeat_post_fix1.notes` → eine Zeile Fakten/Abbruchgrund

## Abbruch

Bei `STORAGE-PROTECTION-*` oder Mount/Permission: Serie stoppen, Evidence trotzdem vollständig, Matrix auf `blocked`/`failed` setzen.
