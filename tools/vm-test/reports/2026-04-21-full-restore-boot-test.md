# Full-Restore + Boot-Test (setuphelfer-a → setuphelfer-b)

Stand: Host-gestützter Lauf mit SSH auf `127.0.0.1:2222` (Quelle) und `127.0.0.1:2223` (Ziel). Kein Git-Commit.

## 1) Restore-Lauf (Fakten)

- `setuphelfer-b`: Zusatzplatten vorbereitet und gemountet:
  - `/dev/sdb1` (`backup-b`) → `/mnt/backup`
  - `/dev/sdc1` (`restore-b`) → `/mnt/target`
- Archiv von `setuphelfer-a` übernommen:
  - Quelle: `/mnt/backup-test/pi-backup-full-20260420_223625.tar.gz`
  - Ziel: `/mnt/backup/pi-backup-full-20260420_223625.tar.gz`
- `restore_files` auf `setuphelfer-b` nach `/mnt/target` ausgeführt:
  - Ergebnis: `RESTORE_ROOT_OK= True`
  - Schlüssel: `backup_recovery.ok`
  - Detail: `None`

## 2) Bootloader / Boot-Vorbereitung (Fakten)

- GRUB-Installation im chroot auf Zielplatte durchgeführt:
  - `grub-install /dev/sdc` → erfolgreich
  - `update-grub` → erfolgreich
- Root-FS-UUID in `/mnt/target/etc/fstab` auf UUID von `/dev/sdc1` gesetzt.
- Laufzeitverzeichnisse im Ziel ergänzt:
  - `/run`, `/run/lock`, `/tmp`
- Dateirechte im Ziel geprüft:
  - `/mnt/target/etc/sudo.conf` → `root:root`
  - `/mnt/target/usr/bin/sudo` → `root:root`, setuid-Bit gesetzt (`-rwsr-xr-x`)

## 3) Boot-Test (Fakten)

- SATA-Port-Mapping für Boottest umgestellt:
  - Port 0: `restore-target-b.vdi` (Boot-Disk)
  - Port 2: `system-b.vdi`
- VM gestartet; SSH-Banner auf `2223` nach Wartezeit vorhanden:
  - `SSH-2.0-OpenSSH_10.0p2 Debian-7+deb13u1`
- SSH-Login erfolgreich:
  - `hostname` auf Zielsystem: `setuphelfer-b`
  - `whoami`: `volker`
  - `sudo -n true`: erfolgreich (`SUDO_OK`)
- Laufwerkssicht nach Boot:
  - `sda1` auf `/` (restaurierte Boot-Disk)
  - `sdb1` auf `/mnt/backup`
  - `sdc1` auf `/mnt/target`

## 4) Setuphelfer-Dienste (Fakten)

- `systemctl is-active ssh` → `active`
- `systemctl is-active setuphelfer-backend` → `inactive`
- `systemctl is-active setuphelfer` → `inactive`
- Zusätzliche Prüfung:
  - `/opt/setuphelfer` fehlt
  - `/etc/setuphelfer` fehlt
  - `/var/log/setuphelfer` fehlt
  - `/var/lib/setuphelfer` fehlt
  - `setuphelfer-backend.service` / `setuphelfer.service` auf dem gebooteten Zielsystem nicht gefunden

## 5) Auffälligkeiten (nur Beobachtungen)

- Während Zwischenständen traten Bootmeldungen zu `mdadm`/`systemd-remount-fs` auf; nach UUID-/Rechtekorrekturen war SSH-Zugang wieder möglich.
- Der Restore repliziert den gesicherten Zustand: Hostname des gebooteten Zielsystems ist `setuphelfer-b`.
- Setuphelfer-Software/Units sind im final gebooteten Restore-Stand nicht vorhanden bzw. nicht aktiv (siehe Abschnitt 4).

## 6) Zielerreichung laut Auftrag

| Kriterium | Status |
|-----------|--------|
| Restore erfolgreich | **Ja** (`RESTORE_ROOT_OK=True`) |
| System bootet | **Ja** (SSH-Banner + Login auf 2223) |
| setuphelfer läuft | **Nein** (`setuphelfer-backend`/`setuphelfer` inactive bzw. Units/Pfade fehlen) |

## 7) Post-Restore-Fix (laufender Zustand wiederhergestellt)

- Repository vom Host nach `setuphelfer-b` gespiegelt (`~/piinstaller-src`).
- `scripts/install-system.sh` auf `setuphelfer-b` non-interaktiv ausgeführt:
  - `SETUPHELFER_NONINTERACTIVE=1`
  - `SETUPHELFER_SYSTEMD_ENABLE=yes`
  - `SETUPHELFER_SYSTEMD_START_NOW=yes`
  - `PI_INSTALLER_USER=volker`
- Ergebnis:
  - `/opt/setuphelfer`, `/etc/setuphelfer`, `/var/log/setuphelfer`, `/var/lib/setuphelfer` wieder vorhanden.
  - `setuphelfer-backend.service` enabled + active.
- Web-UI-Service `setuphelfer.service` initial nicht stabil (Sandbox/OOM/Netlink); mit Drop-In korrigiert:
  - Datei: `/etc/systemd/system/setuphelfer.service.d/override.conf`
  - gesetzt:
    - `SystemCallFilter=`
    - `MemoryMax=0`
    - `Environment=NODE_OPTIONS=--max-old-space-size=1024`
    - `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK`
- Finaler Zustand auf `setuphelfer-b`:
  - `systemctl is-active setuphelfer-backend` → `active`
  - `systemctl is-active setuphelfer` → `active`
  - Listener:
    - Backend: `127.0.0.1:8000` (`python3`)
    - Web-UI: `0.0.0.0:3001` (`node/vite preview`)

## 8) Determinismus-Validierung (ohne manuelle Overrides)

- Installer erneut mit finalem Skript ausgeführt (`SETUPHELFER_NONINTERACTIVE=1`, Start/Enable aktiv).
- Danach explizit geprüft:
  - `/etc/systemd/system/setuphelfer.service.d` **nicht vorhanden**
  - `/etc/systemd/system/setuphelfer-backend.service.d` **nicht vorhanden**
- Laufzustand ohne Drop-In:
  - `systemctl is-active setuphelfer-backend` → `active`
  - `systemctl is-active setuphelfer` → `active`
- Endpunkt-Smoketest:
  - `curl http://127.0.0.1:8000/api/version` → HTTP `200`
  - `curl http://127.0.0.1:3001/` → HTTP `200`

