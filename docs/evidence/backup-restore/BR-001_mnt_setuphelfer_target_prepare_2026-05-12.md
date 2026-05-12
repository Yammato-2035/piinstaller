# BR-001 — Vorbereitung `/mnt/setuphelfer/backups` (Option 2, 2026-05-12)

## Freigabe (Kurz)

Externes Volume **`/dev/sdd1`**, Label **`setuphelfer-back`**, ausschließlich als servicefreundliches Ziel unter **`/mnt/setuphelfer/backups`**. Kein mkfs/dd/Restore/Löschen interner Platten.

## Phase 1 — Device / Mount

| Prüfung | Ergebnis |
|--------|----------|
| `lsblk -f` | `sdd1` ext4, LABEL `setuphelfer-back`, MOUNTPOINTS u. a. **`/mnt/setuphelfer/backups`** und `/media/gabriel/setuphelfer-back` |
| `findmnt -T …/setuphelfer-backups` (media) | `SOURCE=/dev/sdd1`, `ext4`, `rw` |
| `df -h` | `/dev/sdd1`, ausreichend frei (~679 GB) |
| `stat` Ziel | `root:setuphelfer`, `2770` |

**Pflicht erfüllt:** SOURCE **`/dev/sdd1`**, **ext4**, **rw**, nicht `/`/`/home`/…

## Phase 2 — `/mnt/setuphelfer/backups`

**Ist-Zustand:** Verzeichnis existiert; **`findmnt /mnt/setuphelfer/backups`** zeigt bereits **Bind** auf dieselbe Inode-Ebene wie `…/setuphelfer-backups` auf sdd1:

`TARGET=/mnt/setuphelfer/backups` `SOURCE=/dev/sdd1[/setuphelfer-backups]` `FSTYPE=ext4` `rw`

**Keine erneute** `mkdir`/`mount`/`chown`/`chmod`-Ausführung in dieser Session (bereits korrekt; keine Blindänderung). Operator kann bei Bedarf idempotent nachziehen.

## Phase 3 — Dienstnutzer `setuphelfer`

`sudo -n -u setuphelfer test …` / Schreibprobe: **nicht ausführbar** (Passwort für sudo erforderlich).  
**Statisch:** Mountpunkt **`2770`** mit Gruppe **`setuphelfer`** → Mitglied `setuphelfer` sollte **schreiben** können; **verifiziert** wurde es hier nicht per sudo.

## Phase 4 — Deploy `/opt/setuphelfer`

`/opt/setuphelfer/backend` **ohne** Git-Checkout erkannt. **Kein** `systemctl restart` ausgeführt (keine sudo-Freigabe).  
**Hinweis:** Produktions-API **`127.0.0.1:8000`** nutzt bis zum Deploy weiterhin den **alten** Code (ohne findmnt-Flatten / ohne Klammer-Normalisierung).

## Phase 5 — target-check

### Produktion `curl` `127.0.0.1:8000` (vor Deploy des Klammer-Fixes)

Fehlerbeispiel (bereits analysiert): `STORAGE-PROTECTION-004` wegen `mount_source_seen=/dev/sdd1[/setuphelfer-backups]` ohne auflösbare Partition.

### Workspace-Code (nach Fix `safe_device`)

`TestClient` gegen Repo-`app`: **`backup.target_check_ok`** für `backup_dir=/mnt/setuphelfer/backups`, **`mount.target`** = `/mnt/setuphelfer/backups` (nicht mehr `/`).

## Phase 6 — Produktcode (Klammer-SOURCE)

Minimalfix in **`core/safe_device.py`:** `_normalize_findmnt_bracket_block_source` — findmnt-Syntax `/dev/sdX[/sub]` → `/dev/sdX` für Klassifikation. Test: `test_safe_device_storage_protection_v1.TestFindmntBracketBlockSource`.

## BR-001 Ampel

**`blocked`** (Stand Abend 2026-05-12): produktiver `target-check` für `/mnt/setuphelfer/backups` weiterhin **rot** (STORAGE-004, interner nvme-Pfad); Host-Layout wich von der Freigabe **nur sdd1** ab (Label auf **sda1**, sdd1 = anderes Medium). Deploy-Versuch nach `/opt` wurde **zurückgerollt**. Siehe **`BR-001_productive_target_check_2026-05-12.md`**.

**Kein** Backup-Job gestartet.
