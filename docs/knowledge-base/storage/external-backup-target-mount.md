# Externer Mount für BR-001 (`/media/setuphelfer/<label>`)

## Root Cause: irreführendes `STORAGE-PROTECTION-001`

Wenn **`/media/setuphelfer/br001`** (oder ein Unterpfad) **nicht existiert**, ermittelt `validate_write_target` den Mount-Anker über vorhandene Eltern (`/media` → liegt auf **`/`**). Die Klassifikation meldet dann fälschlich **Systemplatte** → **`STORAGE-PROTECTION-001`**.

**Korrekte Diagnose (ab Code-Fix):** **`STORAGE-PROTECTION-007`** — externes Block-FS unter `/media/setuphelfer/…` fehlt oder ist nicht gemountet.

| Situation | Diagnose |
|-----------|----------|
| Pfad fehlt, Anker auf `/` oder `/media` (Root-FS) | **STORAGE-PROTECTION-007** |
| Pfad auf USB/ext4 gemountet, Rechte falsch | **BACKUP-TARGET-PERMISSION-001** |
| Pfad unter `/media/<login>/…` | **BACKUP-TARGET-USER-MOUNT-003** |
| Echtes externes Ziel, alles OK | **target-check success** |

## Echter Mount vs. Fake-Pfad

| | Erlaubt für BR-001 | Blockiert |
|---|-------------------|-----------|
| Verzeichnis auf **`/`** (z. B. nur `mkdir` ohne Mount) | nein | 007 / 001 |
| **Bind-Mount** von USB-Partition nach `/media/setuphelfer/br001` | ja | — |
| **Direkt-Mount** `UUID=…` nach `/media/setuphelfer/br001` | ja | — |
| `/media/gabriel/Backup` als API-`backup_dir` | nein (User-Mount) | 003 |

## Operator: Automatisches Skript

```bash
cd /opt/setuphelfer   # oder Workspace-Root
sudo ./scripts/operator/setup-external-backup-target.sh br001
```

Umgebungsvariablen:

- `SETUPHELFER_USB_UUID` — ext4-Partition (Default: HGST-Backup-UUID aus Lab)
- `SETUPHELFER_MOUNT_MODE` — `bind` (Default) oder `direct`

## Variante A — Direkt-Mount

```bash
export BR001_DIR=/media/setuphelfer/br001
export USB_UUID=44ce6f76-7896-4623-87b0-d81aedbed6d5

sudo install -d -m 0755 /media/setuphelfer
sudo install -d -m 0755 "${BR001_DIR}"
sudo mount -o nosuid,nodev,noatime "UUID=${USB_UUID}" "${BR001_DIR}"
sudo chown root:setuphelfer "${BR001_DIR}"
sudo chmod 0770 "${BR001_DIR}"

findmnt -T "${BR001_DIR}"
sudo -u setuphelfer touch "${BR001_DIR}/.write_probe" && sudo -u setuphelfer rm -f "${BR001_DIR}/.write_probe"

curl -sG 'http://127.0.0.1:8000/api/backup/target-check' --data-urlencode "backup_dir=${BR001_DIR}" | jq .
```

## Variante B — Bind-Mount (udisks → setuphelfer)

Wenn die Platte bereits unter z. B. `/media/gabriel/Backup` hängt:

```bash
export BR001_DIR=/media/setuphelfer/br001
export USB_SRC=/media/gabriel/Backup

sudo install -d -m 0755 /media/setuphelfer
sudo install -d -m 0755 "${BR001_DIR}"
sudo mount --bind "${USB_SRC}" "${BR001_DIR}"
sudo chown root:setuphelfer "${BR001_DIR}"
sudo chmod 0770 "${BR001_DIR}"

findmnt -T "${BR001_DIR}"
curl -sG 'http://127.0.0.1:8000/api/backup/target-check' --data-urlencode "backup_dir=${BR001_DIR}" | jq .
```

**Wichtig:** `backup_dir` in der API ist **`/media/setuphelfer/br001`**, nicht der udisks-Pfad.

## fstab-Beispiel (optional, Admin)

```fstab
UUID=44ce6f76-7896-4623-87b0-d81aedbed6d5  /media/setuphelfer/br001  ext4  nosuid,nodev,noatime  0  2
```

Nach Änderung: `sudo mount -a`, Rechte wie oben, `systemctl restart setuphelfer-backend.service`.

## FAQ

### Warum nicht einfach `/media/gabriel/Backup` in der API?

Der Dienst läuft als **`setuphelfer`**, nicht als Desktop-Login; udisks-Mounts sind oft **0700**. Bind nach **`/media/setuphelfer/…`** mit **`root:setuphelfer`** und **0770** ist der vorgesehene Weg.

### Warum kein `chmod 777`?

World-writable Ziele umgehen Mandantentrennung und Rescue-Schutzlinien.

## Siehe auch

- `external-backup-target-architecture.md`
- `docs/evidence/runtime-results/handoff/BR001_operator_final_execution_handoff.md`
