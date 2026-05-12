# BR-001 — Device-/Mount-Baseline (nur lesend, 2026-05-12)

**Modus:** STRICT — keine Schreib-, Mount-, Deploy- oder Service-Operationen.  
**Hostname:** `volker-ROG-Strix` (laut vorheriger Evidence).  
**Zweck:** Eindeutige Baseline vor erneutem BR-001 / Deploy / target-check.

---

## Phase 1 — System- und Device-Snapshot (Rohauszüge)

### `lsblk -o NAME,PATH,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL,SERIAL,TRAN`

```text
NAME        PATH             SIZE FSTYPE LABEL            UUID                                 MOUNTPOINTS                     MODEL                        SERIAL          TRAN
sda         /dev/sda         1,8T                                                                                              Samsung SSD 970 EVO Plus 2TB S4J4NM0W300640J usb
├─sda1      /dev/sda1      931,5G ext4   setuphelfer-back adbd53e5-26fd-4723-b0f1-1880dbaa2719 /media/gabriel/setuphelfer-back                                              
└─sda2      /dev/sda2      931,5G ntfs   windows-backup   01BDA42D54D84B41                     /media/gabriel/windows-backup                                                
sdb         /dev/sdb        59,5G                                                                                              SD/MMC                       058F84688461    usb
└─sdb1      /dev/sdb1       59,5G vfat   SDCARD1          7007-B24C                            /media/gabriel/SDCARD1                                                       
sdc         /dev/sdc           0B                                                                                              Micro SD/M2                  058F84688461    usb
sdd         /dev/sdd          59G                                                                                              Ultra Line                   24111412110212  usb
└─sdd1      /dev/sdd1         59G exfat  INTENSO          01C0-0220                            /media/gabriel/INTENSO                                                       
nvme0n1     /dev/nvme0n1     1,8T                                                                                              Samsung SSD 980 PRO 2TB      S736NL0X905338X nvme
├─nvme0n1p1 /dev/nvme0n1p1   512M vfat                    94A7-F964                            /boot/efi                                                                    nvme
└─nvme0n1p2 /dev/nvme0n1p2   1,8T ext4                    57b5dd3e-2461-41f2-821a-3c81ed058dcd /                                                                            nvme
nvme1n1     … (weitere NTFS/vfat-Partitionen, ohne aktuelle MOUNTPOINTS in lsblk-Auszug)
```

### `findmnt -R /mnt/setuphelfer` / `findmnt -R /media/gabriel`

- **`findmnt -R /mnt/setuphelfer`:** keine Zeilen (kein als Unterbaum gemounteter FS unter diesem Pfad im Sinne von `findmnt -R` hier sichtbar).
- **`findmnt -R /media/gabriel`:** (in dieser Session) leerer Auszug im Log — relevante Einzelmounts siehe `findmnt -T` und `mount` unten.

### `findmnt -T /mnt/setuphelfer/backups`

```text
TARGET SOURCE         FSTYPE OPTIONS
/      /dev/nvme0n1p2 ext4   rw,relatime,errors=remount-ro
```

**Interpretation:** Der Pfad `/mnt/setuphelfer/backups` liegt auf dem **gleichen Dateisystem wie `/`** — **interne NVMe-Root-Partition** (`/dev/nvme0n1p2`), nicht auf dem USB-Volume mit Label `setuphelfer-back`.

### `findmnt -T /media/gabriel/setuphelfer-back`

```text
TARGET                          SOURCE    FSTYPE OPTIONS
/media/gabriel/setuphelfer-back /dev/sda1 ext4   rw,nosuid,nodev,relatime,errors=remount-ro,stripe=8191
```

### `blkid` (Auszug — nicht alle USB-Partitionen in diesem Lauf gelistet)

```text
/dev/nvme0n1p1: UUID="94A7-F964" … TYPE="vfat" …
/dev/nvme0n1p2: UUID="57b5dd3e-2461-41f2-821a-3c81ed058dcd" … TYPE="ext4" …
… (weitere nvme1n1-Partitionen ntfs/vfat)
```

**Hinweis:** UUID/LABEL der USB-Partition **`/dev/sda1`** sind zuverlässig aus **`lsblk`** ersichtlich: **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, Label **`setuphelfer-back`**.

### `df -hT` (relevant)

| Dateisystem   | Typ   | Eingehängt auf |
|---------------|-------|----------------|
| `/dev/nvme0n1p2` | ext4 | `/` |
| `/dev/nvme0n1p1` | vfat | `/boot/efi` |
| `/dev/sdb1`   | vfat  | `/media/gabriel/SDCARD1` |
| `/dev/sda1`   | ext4  | `/media/gabriel/setuphelfer-back` |
| `/dev/sdd1`   | exfat | `/media/gabriel/INTENSO` |
| `/dev/sda2`   | fuseblk | `/media/gabriel/windows-backup` |

### `mount | grep -E 'setuphelfer|gabriel|sda|sdd|nvme'` (Auszug)

- `/` und `/boot/efi` auf **nvme0n1**.
- **`/dev/sda1`** → **`/media/gabriel/setuphelfer-back`** (ext4, rw, udisks2).
- **`/dev/sdd1`** → **`/media/gabriel/INTENSO`** (exfat, rw).
- weitere: `sdb1` (SDCARD1), `sda2` (windows-backup).

### `stat /mnt/setuphelfer/backups` (lesend)

- **Gerät:** `259/9` (typisch für NVMe-/Block-Stack des Root-FS, konsistent mit `findmnt -T` → `/`).
- **Modus:** `2770`, `root:setuphelfer`.

---

## Phase 1 — Erfassung (Antworten auf die Prüfliste)

| Frage | Ergebnis |
|--------|----------|
| Alle Geräte mit Label **`setuphelfer-back`** | **Eines:** **`/dev/sda1`**, ext4, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, TRAN **usb**, Mount **`/media/gabriel/setuphelfer-back`**. |
| Alle **ext4**-Wechseldatenträger (lsblk: usb + gemountet) | **`/dev/sda1`** (setuphelfer-back) — Root **`/dev/nvme0n1p2`** ist ext4, aber **intern nvme**, kein USB. |
| Mountpoints unter **`/mnt/setuphelfer`** | Verzeichnisbaum existiert (`backups`, `cache`, …); **kein** separates `findmnt`-Ziel für `backups` als eigenes FS — liegt auf `/`. |
| Mountpoints unter **`/media/gabriel`** | u. a. `setuphelfer-back`, `INTENSO`, `SDCARD1`, `windows-backup`. |
| Ist **`/mnt/setuphelfer/backups`** extern? | **Nein** — `findmnt -T` zeigt **`/`** / **`/dev/nvme0n1p2`**. |
| Liegt es unter interner NVMe? | **Ja** — gleiches FS wie Root (`nvme0n1p2`). |

---

## Phase 2 — Konsistenzprüfung (1–10)

| # | Kriterium | Ergebnis |
|---|-----------|----------|
| 1 | Genau ein externes Backupmedium? | **Nein** — mehrere USB-/Removable-Geräte (`sda` mit zwei Partitionen, `sdb`, `sdd`; `sdc` 0B). |
| 2 | Eindeutige UUID für das **setuphelfer-back**-Volume? | **Ja** für **`/dev/sda1`:** `adbd53e5-26fd-4723-b0f1-1880dbaa2719`. |
| 3 | Stimmen Label, UUID, Device, Mount für dieses Volume? | **Ja** — konsistent: **`setuphelfer-back`** auf **`sda1`** → **`/media/gabriel/setuphelfer-back`**. |
| 4 | Ist `/mnt/setuphelfer/backups` auf dieses Medium gemountet oder gebunden? | **Nein** — kein Bind/Separatmount sichtbar; Pfad liegt auf **Root-FS**. |
| 5 | Zeigt `findmnt -T /mnt/setuphelfer/backups` das externe Medium? | **Nein** — zeigt **`/`** / **`nvme0n1p2`**. |
| 6 | Externes setuphelfer-back-Medium rw? | **Ja** (`rw` in `findmnt` / `mount` für `sda1`). |
| 7 | Externes Volume nicht Root/home/tmp/var als Mount? | **`/media/gabriel/setuphelfer-back`** — nicht Root; **Pfad BR-001-Ziel** `/mnt/...` liegt aber auf Root-FS (Widerspruch zum gewünschten externen Ziel). |
| 8 | Nicht Windows/EFI/Boot als Zielpfad? | **`/mnt/setuphelfer/backups`** ist nicht EFI; es ist **Systemplatte `/`**. |
| 9 | Nicht interner NVMe-Mount für **diesen** Pfad? | **`/mnt/setuphelfer/backups`:** **intern** (nvme0n1p2). |
|10| Widersprüchliche Labels / Mehrfachmounts? | Label **`setuphelfer-back`** nur einmal; **mehrere** externe Medien parallel — keine doppelte gleiche Partition, aber **Mehrdeutigkeit „das eine Backupmedium“**. |

**Gesamt Phase 2:** **Widersprüchlich / nicht eindeutig** für BR-001-Pfad **`/mnt/setuphelfer/backups`** als externes Ziel. **BR-001 bleibt blocked.**

---

## Phase 3 — Freigabeempfehlung

**Widerruf / Übersteuerung (Betreiber, 2026-05-12):** Eine etwaige frühere Empfehlung, **`/mnt/setuphelfer/backups`** per **Bind** anzubinden, ist **unzulässig**. Maßgeblich ist ausschließlich: **`/media/gabriel/setuphelfer-back`** (bzw. namentlich freigegebener Unterordner darunter). Details: **`BR-001_path_policy_correction_2026-05-12.md`**.

**Betreiber-Freigabe (aktuell):**

| Feld | Wert |
|------|------|
| Gerät | **`/dev/sda1`** (`sda`) |
| Pfad | **`/media/gabriel/setuphelfer-back`** |
| FS / Label / UUID | **ext4** / **setuphelfer-back** / **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`** |
| Größe (Partition) | ca. **931,5 G** |

**Nicht zulässig:** **`/mnt/setuphelfer/backups`**, **Bind**, andere `/media/...`-Ziele, **sdb1/sdd1**/INTENSO/windows-backup, interne NVMe als BR-001-Ziel.

**Muster-Freigabetext (Betreiber, ohne Bind):**

```text
Freigegeben wird ausschließlich:
UUID=adbd53e5-26fd-4723-b0f1-1880dbaa2719
LABEL=setuphelfer-back
Mount-Ziel=/media/gabriel/setuphelfer-back
Filesystem=ext4
Device aktuell=/dev/sda1
Begründung=extern (usb), rw; kein /mnt/setuphelfer/backups; kein Bind
```

## Phase 4 — Produktiv-Deploy (nur dokumentiert, nicht ausgeführt)

| Punkt | Wert |
|--------|------|
| Produktiver Backend-Pfad | **`/opt/setuphelfer/backend`** |
| Git-Repo unter `/opt/.../backend`? | **Nein** |
| Laufende API (lesend `GET /api/version`) | **`1.5.0.0`**, `install_profile`: **`opt`**, `app_edition`: **`release`** |
| Deployverfahren (bekannt, nicht ausgeführt) | Abgleich Workspace-Dateien (z. B. `app.py`, `core/safe_device.py`) mit `/opt/...`, Backup der alten Dateien, **`sudo systemctl restart setuphelfer-backend`** |
| Vor erneutem Deploy zu klären | **(1)** Betreiberpfad ausschließlich `/media/gabriel/setuphelfer-back` (kein `/mnt/…`, kein Bind). **(2)** Produktiver `target-check` auf genau diesem Pfad grün (aktuell STORAGE-001). **(3)** Dienstnutzer-Traverse/Schreibprobe verifizieren. **(4)** sudo für Restart falls Deploy nötig. |

---

## Phase 5 — Verweise

- Maschinenlesbar: **`BR-001_device_mount_baseline_2026-05-12.json`**
- Gesamt-BR-001: **`BR-001.json`**

---

## Abnahme (diese Baseline)

| Kriterium | Erfüllt? |
|-----------|----------|
| Device-/Mount-Lage eindeutig dokumentiert | **Ja** (inkl. Widerspruch BR-Pfad vs. externes Volume) |
| Keine Schreiboperation | **Ja** |
| BR-001 nur bei eindeutiger UUID/Mount freigeben | **Vorgabe eingehalten** — Zielpfad ist **`/media/gabriel/setuphelfer-back`** laut Betreiber; **`/mnt/setuphelfer/backups`** ist **kein** BR-001-Ziel. BR-001 bleibt **blocked**, bis API + Dienstnutzer grün sind (siehe **`BR-001_path_policy_correction_2026-05-12.md`**). |

---

## Nachtrag (2026-05-12) — Shell vs. API

Siehe **`BR-001_productive_target_check_media_path_analysis_2026-05-12.md`**: **STORAGE-001** entsteht v. a. durch **fehlenden Traverse** für **`setuphelfer`** unter **`/media/gabriel`** und nachfolgende **Anker-/findmnt-Auflösung** auf **`/`** / **`nvme0n1p2`** — nicht durch falsches Label am Zielmount selbst.
