# Laufwerks-Klon – Architektur

**Erstellt:** 2026-02-06  
**Status:** Implementiert  
**Modul:** Backup & Wiederherstellen → Laufwerk klonen

---

## 1. Zielsetzung

Eine **Clone-Funktion** in PI-Installer, mit der das laufende System (Root-Dateisystem von der SD-Karte) auf ein Ziellaufwerk (z.B. NVMe, USB-SSD) geklont werden kann. Nach dem Klonen und Anpassung der Boot-Konfiguration startet der Raspberry Pi von dem neuen Laufwerk (Hybrid-Boot: Kernel von SD, Root von NVMe/USB).

---

## 2. Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend (BackupRestore.tsx)                     │
│  ┌──────────┬──────────┬──────────┬──────────────┐                      │
│  │ Backup   │ Wiederh. │ Einstell.│ Laufwerk     │  ← Neuer Tab         │
│  │          │          │          │ klonen       │                      │
│  └──────────┴──────────┴──────────┴──────────────┘                      │
│       │                                 │                               │
│       │                                 │ GET /api/backup/clone/disk-info│
│       │                                 │ POST /api/backup/clone         │
│       │                                 │ GET /api/backup/jobs/{id}      │
└──────┼─────────────────────────────────────┼─────────────────────────────────┘
       │                                 │
       ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (app.py)                                 │
│                                                                          │
│  GET  /api/backup/clone/disk-info   → Quell-/Ziel-Laufwerke auflisten    │
│  POST /api/backup/clone             → Klon-Job starten (async)           │
│  GET  /api/backup/jobs/{id}         → Job-Status (shared mit Backup)     │
│                                                                          │
│  Klon-Logik (Thread):                                                    │
│    1. Ziellaufwerk mounten (/mnt/pi-installer-clone)                     │
│    2. rsync von / nach Ziel (exclude boot, /proc, /sys, /dev, /mnt)      │
│    3. fstab auf Ziel anpassen (root=/dev/xxx)                            │
│    4. cmdline.txt auf Boot-Partition anpassen (root=/dev/xxx)            │
│    5. Ziel unmounten                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Datenfluss

### 3.1 Laufwerks-Erkennung (disk-info)

| Eingabe | Ausgabe |
|---------|---------|
| - | `source`: Root-Device, Boot-Device, Mountpoint |
| - | `targets`: Liste ext4-Partitionen (NVMe, USB) außer Root/Boot |
| - | `boot_partition`: Pfad zur Boot-Partition (z.B. /boot/firmware) |

**Quell-Laufwerk:** Partition, die unter `/` gemountet ist (via findmnt oder /proc/mounts).

**Ziel-Kandidaten:**
- ext4-Partitionen
- Keine Root-/Boot-Partition
- NVMe, USB, SATA (keine SD-Karte, falls SD = Quelle)
- Optional: Nur gemountet ODER ungemountet (Backend mounted bei Bedarf)

### 3.2 Klon-Ablauf

| Schritt | Aktion |
|---------|--------|
| 1 | Validierung: Ziel ext4, genug Platz, nicht Root |
| 2 | Mount-Ziel bei `/mnt/pi-installer-clone` (falls nicht gemountet) |
| 3 | `rsync -axHAWXS --numeric-ids / /mnt/pi-installer-clone/` mit Excludes |
| 4 | `/mnt/pi-installer-clone/etc/fstab` anpassen (Root-Zeile → Ziel-Device) |
| 5 | `/boot/firmware/cmdline.txt` anpassen (`root=/dev/xxx`) |
| 6 | Unmount Ziel |

**Excludes:**
- `/boot`, `/boot/firmware` (bleiben auf SD)
- `/proc`, `/sys`, `/dev`, `/tmp`, `/run`, `/mnt`, `/lost+found`
- `/mnt/pi-installer-clone` (Ziel selbst)

---

## 4. API-Spezifikation

### GET /api/backup/clone/disk-info

**Response:**
```json
{
  "status": "success",
  "source": {
    "device": "/dev/mmcblk0p2",
    "mountpoint": "/",
    "size": "118.6G",
    "fstype": "ext4",
    "model": "..."
  },
  "boot": {
    "mountpoint": "/boot/firmware",
    "device": "/dev/mmcblk0p1"
  },
  "targets": [
    {
      "device": "/dev/nvme0n1p1",
      "name": "nvme0n1p1",
      "size": "476.9G",
      "fstype": "ext4",
      "mounted": false,
      "mountpoint": null,
      "model": "INTEL SSDPEKNU512GZ",
      "tran": "nvme"
    }
  ]
}
```

### POST /api/backup/clone

**Request:**
```json
{
  "target_device": "/dev/nvme0n1p1",
  "sudo_password": "..."
}
```

**Response (async):**
```json
{
  "status": "accepted",
  "job_id": "abc123def456",
  "message": "Klon-Job gestartet"
}
```

### Job-Status (GET /api/backup/jobs/{job_id})

Gleiche Struktur wie Backup-Jobs. Zusätzlich:
- `type`: "clone"
- `target_device`: "/dev/nvme0n1p1"
- `clone_progress_pct`: optional (wenn rsync --info=progress2 geparst wird)

---

## 5. Frontend-UI

### Tab „Laufwerk klonen“

- **Quelle:** Read-only Anzeige (aktuelles Root: z.B. SD-Karte mmcblk0p2)
- **Ziel:** Dropdown/Liste der Ziel-Laufwerke (NVMe, USB)
- **Info-Box:** Hinweis auf Hybrid-Boot (Boot bleibt auf SD, Root wechselt)
- **Button:** „System klonen“
- **Fortschritt:** Job-Polling wie bei Backup (Lauf-Anzeige, Ergebnisse)

### Validierung

- Ziel muss ext4 sein
- Ziel darf nicht Root/Boot sein
- Ziel-Größe ≥ Quell-Belegung (grobe Prüfung)

---

## 6. Sicherheitsaspekte

- **Sudo erforderlich:** Mount, rsync, Bearbeitung von fstab/cmdline.txt
- **Abbruch:** Cancel während rsync setzt Abbruch-Flag; rsync läuft bis Ende, danach wird „cancelled“ zurückgegeben (kein sofortiger Prozess-Kill)
- **Kein Überschreiben der Quelle:** Ziel darf nie Root sein
- **Idempotenz:** Mehrfaches Klonen möglich (Ziel wird überschrieben)
- **Rollback:** SD-Karte behält Boot + alte cmdline.txt → bei Problemen einfach cmdline.txt zurücksetzen

---

## 7. Abhängigkeiten

- `rsync` (in der Regel vorinstalliert)
- `findmnt` / `lsblk` (util-linux)
- Root/Sudo-Zugriff

---

## 8. Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app.py` | Endpoints `/api/backup/clone/disk-info`, `/api/backup/clone`, Klon-Logik |
| `frontend/src/pages/BackupRestore.tsx` | Tab „Laufwerk klonen“, UI, API-Calls |
| `docs/CLONE_ARCHITECTURE.md` | Diese Architektur-Dokumentation |
