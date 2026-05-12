# BR-001 — Service-User-Zielzugriff und target-check (Analyse 2026-05-12)

## Zielpfad

`/media/gabriel/setuphelfer-back/setuphelfer-backups`

## Phase 1 — Ist-Zustand (Shell, 2026-05-12)

| Prüfung | Ergebnis |
|--------|----------|
| `realpath` | `/media/gabriel/setuphelfer-back/setuphelfer-backups` |
| `findmnt -T` | `TARGET=/media/gabriel/setuphelfer-back` `SOURCE=/dev/sdd1` `FSTYPE=ext4` |
| `df -h` | `/dev/sdd1` auf genanntem Mount, ~679 GB frei |
| `lsblk -f` | `sdd1` ext4, Label `setuphelfer-back`; **zwei** Mountpoints: `/mnt/setuphelfer/backups` und `/media/gabriel/setuphelfer-back` (gleiche Partition) |

### `stat` (Kurz)

| Pfad | Modus | Owner:Group |
|------|-------|---------------|
| `/media` | `0755` `drwxr-xr-x` | `root:root` |
| `/media/gabriel` | `0750` `drwxr-x---` | `root:root` |
| `/media/gabriel/setuphelfer-back` | `2770` `drwxrws---` | `root:setuphelfer` |
| `…/setuphelfer-backups` | `2770` `drwxrws---` | `root:setuphelfer` |

### `getfacl` (Auszug)

- **`/media`:** Standard-UNIX, `other::r-x` → world traverse möglich.
- **`/media/gabriel`:** `user:gabriel:r-x`, `group::r-x`, **`other::---`** → nur root, Gruppe root (nur r-x auf Verzeichnis), und **ACL-User gabriel** haben Traverse.
- **`…/setuphelfer-back` / `…/setuphelfer-backups`:** setgid `setuphelfer`, `group::rwx`, `other::---` — Zugang für Mitglieder der Gruppe `setuphelfer`.

### Identitäten

- **`id gabriel`:** u.g. `setuphelfer` (1001) in Gruppen → **Traverse auf `/media/gabriel` via ACL** + Gruppe auf dem Volume.
- **`id setuphelfer`:** nur `Gruppen=1001(setuphelfer)` — **keine** `gabriel`-ACL auf `/media/gabriel` → **kein Execute auf `/media/gabriel`** → Pfad zum Ziel für den Dienst **nicht traversierbar**.
- **`systemctl show setuphelfer-backend.service`:** `User=setuphelfer`, `Group=setuphelfer`, `SupplementaryGroups=setuphelfer`.

## Phase 2 — `sudo -u setuphelfer` (Traverse/Schreibprobe)

`sudo -n -u setuphelfer test …` war **nicht ausführbar** (Passwort erforderlich).  
Schlussfolgerung daher **statisch** aus POSIX/ACL: **A) Traverse auf `/media/gabriel` für `setuphelfer` verneint.**

**Keine** Schreibprobe-Testdatei auf dem Medium erzeugt (Vorgabe).

## Phase 3 — API / Code (`target-check`)

### Produktion `127.0.0.1:8000`

- `GET /api/backup/target-check?backup_dir=<Ziel>` endete zuvor mit `backup.path_invalid` / **`STORAGE-PROTECTION-001`**, sobald `_validate_backup_dir` → `validate_write_target` im **Dienstkontext** scheitert (siehe Phase 4).

### Falsches JSON-Feld `mount` mit `TARGET=/` (Beobachtung unter gabriel / TestClient)

**Ursache C (Code):** `_findmnt_mounts()` in `backend/app.py` lieferte nur die **Top-Level**-Einträge des `findmnt -J`-Baums. Unterknoten stehen unter `children` und wurden **ignoriert**.  
`_best_mount_for_path` iterierte damit praktisch nur den Wurzelknoten (`/`). Zusätzlich matcht die Bedingung `path_str.startswith(tgt.rstrip("/") + "/")` für `tgt="/"` jeden absoluten Pfad (`"" + "/"` → Präfix `/`). Dadurch wurde fälschlich **`/` / nvme** als „bester“ Mount gewählt — **irreführend**, nicht die Safety-Allowlist geschwächt.

**Fix (minimal, Phase 6):** `_flatten_findmnt_filesystems()` eingeführt; `_findmnt_mounts()` liefert die **flache** Liste aller Knoten. Längster passender `TARGET` ist dann z. B. `/media/gabriel/setuphelfer-back`, nicht `/`.

**Kein** Ändern von `validate_write_target` / Allowlist.

## Phase 4 — Ursachenklassifikation (A–F)

| ID | Trifft zu? | Kurz |
|----|------------|------|
| **A** | **Ja** | `setuphelfer` kann `/media/gabriel` nicht traversieren (0750 + ACL nur `gabriel`). |
| **B** | **Teilweise** | Pfad liegt unter sitzungs-/desktop-spezifischem `/media/<user>/…` — für systemd-Dienste ohne Zusatz-ACL ungeeignet. |
| **C** | **Ja** (behoben im Repo) | findmnt-Baum nicht geflacht + Root-Match zu breit → falsches `mount`-Objekt. |
| **D** | **Nein** | `/media` bleibt für `validate_write_target` grundsätzlich zulässig, sofern Blockdevice und Klassifikation passen. |
| **E** | **Nein** | Gleicher Codepfad im Repo; Abweichung = Laufzeituser + alter Deploy bis Update. |
| **F** | — | nicht nötig |

## Phase 5 — Fix-Optionen (nur dokumentiert / teilweise umgesetzt)

### Option 1 — ACL (schneller Test)

- `setfacl -m u:setuphelfer:rx /media/gabriel` (und ggf. weitere Segmente), Ziel `rwx` für Gruppe/ACL wie betriebenlich nötig.  
- **Vorteil:** schnell. **Nachteil:** an Desktop-User-Pfad gekoppelt; **ohne Freigabe nicht ausgeführt** (Vorgabe).

### Option 2 — Produktpfad `/mnt/setuphelfer/backups`

- Externes Volume zusätzlich oder per **Bind-Mount** unter `/mnt/setuphelfer/backups`, Besitz `root:setuphelfer`, `2770`, Dienst in `SupplementaryGroups=setuphelfer`.  
- **Vorteil:** stabil für Dienst. **Nachteil:** saubere Mount-/Fstab-Disziplin nötig; **ohne Freigabe kein Live-Mount ausgeführt**.

### Option 3 — Diagnose im Produkt (umgesetzt: Teil)

- findmnt-Flatten → korrektes `mount` in `target-check`.  
- Optional später: eigener API-Code für **Traverse verweigert** (`PermissionError` / `EACCES`) statt generischem Chain zu `STORAGE-001` — **nicht** in diesem Patch (keine Policy-Abschwächung).

## Phase 7 — Tests

Ausgeführt:

```bash
cd backend && PYTHONPATH=. /tmp/piinstaller-ci-venv/bin/python -m pytest \
  tests/test_backup_findmnt_mount_flatten_v1.py \
  tests/test_safe_device_storage_protection_v1.py \
  tests/test_preflight_backup_v1.py -q
```

Ergebnis: **25 passed**.

## Empfehlung

1. **Deploy** des Repo-Fixes (findmnt-Flatten) auf die produktive Unit, damit `mount` in Logs/API nicht irreführend ist.  
2. **Betrieb:** Option 1 **oder** 2 mit expliziter Freigabe, bis `setuphelfer` den Zielpfad traversieren und `_validate_backup_dir` erfolgreich durchlaufen kann.  
3. Erst danach: Backup-Job starten (`target-check` + Service-User-Schreibprobe grün).

## Nachtrag — Option 2 (`/mnt/setuphelfer/backups`, 2026-05-12)

- **`/mnt/setuphelfer/backups`** ist auf dem Mess-Host bereits als **Bind** auf das externe **`/dev/sdd1`**-Volume (Unterpfad `setuphelfer-backups`) eingerichtet; `root:setuphelfer`, **`2770`**.
- **Zusätzlicher Codefix:** findmnt liefert `SOURCE=/dev/sdd1[/setuphelfer-backups]` — `safe_device` normalisiert das nun auf **`/dev/sdd1`** (keine Allowlist-Lockernung). Siehe `BR-001_mnt_setuphelfer_target_prepare_2026-05-12.md`.
- **Produktion:** Deploy + `systemctl restart setuphelfer-backend` ausstehend; **`sudo -u setuphelfer`**-Tests ausstehend (sudo-Passwort).

## Abnahme (STRICT)

- Ursache **A + C** dokumentiert; **C** im Produktcode minimal behoben (Flatten).  
- **Keine** Abschwächung von `safe_device`/Allowlist.  
- **Kein** Backup-Job gestartet.
