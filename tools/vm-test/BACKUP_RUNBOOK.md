# Backup-Runbook (im Gast + Setuphelfer)

Voraussetzung: OS installiert, `in-guest-setup.sh` ausgeführt, `00-bootstrap-full-recovery-vbox.sh` auf dem Host bereits gelaufen.

## 1. Backup-Disk identifizieren

Im Gast:

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS,FSTYPE
```

Die **zweite** Festplatte (von VirtualBox an Port 1) ist typischerweise `sdb` oder `nvme0n2` — **nicht** die Platte mit `/` (Root).

## 2. Partitionieren und mounten

**Achtung:** Nur die Backup-Disk ansprechen (z. B. `/dev/sdb`), nicht die Systemplatte.

Beispiel (MBR, eine Partition, ext4):

```bash
sudo fdisk /dev/sdb   # n, p, Enter, Enter, w
sudo mkfs.ext4 -L backup-test /dev/sdb1
sudo mount /dev/sdb1 /mnt/backup-test
```

Optional `/etc/fstab` mit `nofail` für dauerhaftes Mount — für Tests reicht manuelles `mount`.

## 3. Setuphelfer-Backup starten

- Setuphelfer-UI oder CLI gemäß Produkt-Dokumentation.
- Ziel: gemountetes Backup-Verzeichnis (z. B. `/mnt/backup-test` oder Unterordner), so dass Manifest und Daten auf der **backup.vdi** landen.

## 4. Ergebnis prüfen

- **Manifest** vorhanden (Dateiname/Format laut Setuphelfer-Doku).
- **Checksummen** oder Signatur-Dateien, falls vorgesehen, vorhanden und konsistent.
- **Verzeichnisstruktur** entspricht der erwarteten Backup-Struktur (keine leeren Kernverzeichnisse ohne erklärbaren Grund).

## Logging (Host)

Nach dem Backup oder bei Fehlern auf dem **Host** (nicht im Gast):

```bash
cd tools/vm-test
./scripts/09-collect-diagnostics.sh
```

Logs: `logs/diagnostics-*.txt`.
