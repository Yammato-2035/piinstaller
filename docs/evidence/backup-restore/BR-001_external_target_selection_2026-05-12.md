# BR-001 — Externe Kandidaten (nur lesend, 2026-05-12)

**Hostname:** volker-ROG-Strix (Evidence-Umgebung)  
**Befehle:** `lsblk`, `df -hT` (Auszüge dokumentiert). **Kein** `mkfs`, **kein** `dd`, **kein** Backup.

## Kurzfassung

- **Bester externer Kandidat für Daten-Backup (ext4, viel frei):** **`/dev/sda1`**, LABEL **setuphelfer-back**, UUID **`adbd53e5-26fd-4723-b0f1-1880dbaa2719`**, aktuell gemountet auf **`/media/gabriel/setuphelfer-back`**, TRAN **usb**, ROTA **1** (externe SSD-Klasse über USB).
- **`/media/setuphelfer/setuphelfer-back`:** auf diesem System **nicht** vorhanden — **nicht** angelegt (Freigabe/Mount-Konzept offen; kein Bind ohne Freigabe).
- **Interne NVMe** (`nvme0n1` mit `/`, `nvme1n1` ohne sicheren Backup-Mount): **keine** Backup-Ziele.

## Kandidatenliste

| Priorität | Device | UUID | Label | FS | Größe | frei (df) | Mountpoint | TRAN | ROTA | RM | extern | Risiko | Empfehlung |
|-----------|--------|------|-------|-----|-------|-----------|--------------|------|------|----|--------|--------|------------|
| 1 (SSD ext) | /dev/sda1 | adbd53e5-… | setuphelfer-back | ext4 | ~931G | ~679G frei (22% belegt) | /media/gabriel/setuphelfer-back | usb | 1 | 0 | ja | ntfs-Schwesterpartition auf sda (Windows-Backup) getrennt | **Primär externes Backup-Ziel** (bereits gemountet) |
| 5 | /dev/sdb1 | 7007-B24C | SDCARD1 | vfat | 59G | ~60G fast leer | /media/gabriel/SDCARD1 | usb | 1 | 1 | ja | vfat, SD, weniger robust | nur nach Freigabe / wenn ext4-Ziel nicht verfügbar |
| 4 | /dev/sdd1 | 01C0-0220 | INTENSO | exfat | 59G | ~59G frei | /media/gabriel/INTENSO | usb | 1 | 1 | ja | exfat, klein | Stick-Klasse; nicht bevorzugt gegenüber sda1 |
| — | /dev/sda2 | 01BDA42D… | windows-backup | fuseblk (NTFS) | ~932G | viel frei | /media/gabriel/windows-backup | usb | 1 | 0 | nein (Windows-Daten) | **nicht** als Setuphelfer-Backup-Ziel |
| — | nvme0n1p2 | 57b5dd3e-… | — | ext4 | 1,8T | — | / | nvme | 0 | 0 | **nein** | Systemplatte | **gesperrt** |
| — | nvme0n1p1 | 94A7-F964 | — | vfat | 512M | — | /boot/efi | nvme | 0 | 0 | **nein** | EFI | **gesperrt** |
| — | nvme1n1* | — | — | ntfs/vfat… | — | — | nicht für Backup gemountet | nvme | 0 | 0 | **nein** | Windows/intern | **gesperrt** |

## Gewählter Kandidat (für „extern vor intern“)

**`/dev/sda1`** (ext4, **setuphelfer-back**) — eindeutig **extern** (USB), **nicht** Root, rw, ausreichend frei.

## Pfad `/media/setuphelfer/setuphelfer-back`

- **Status:** nicht angelegt, nicht gemountet.
- **Begründung:** ohne Betreiberfreigabe kein neuer Mount/Bind; bestehendes externes Ziel liegt unter **`/media/gabriel/setuphelfer-back`**.
- **target-check** gegen diesen Pfad auf **produktivem** Backend (alter Stand): siehe `BR-001_backend_deploy_status_2026-05-12.md`.

## Nächste Freigaben (Betrieb)

1. Backend auf Workspace-Stand deployen (**sudo** für `/opt` + `systemctl restart` — hier **blockiert**, Passwort nötig).  
2. Entscheidung: strategischer Pfad **`/media/setuphelfer/...`** vs. bestehendes **`/media/gabriel/...`**.  
3. Falls **`/media/setuphelfer/...`:** Mount/udev/Betreiberdoku — **ohne** Datenverlust, **ohne** automatische Formatierung.
