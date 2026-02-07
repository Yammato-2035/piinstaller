# Pfade und NVMe-Boot

**Erstellt:** 2026-02-06  
**Zweck:** Dokumentation kritischer Pfade, insbesondere nach NVMe-Clone (Hybrid-Boot)

---

## 1. NVMe-Boot (Hybrid)

Nach dem Klonen auf NVMe gilt:

| Mountpoint        | Device        | Beschreibung                    |
|-------------------|---------------|---------------------------------|
| `/` (root)        | `/dev/nvme0n1p1` | Root-Dateisystem (NVMe)       |
| `/boot/firmware`  | `/dev/mmcblk0p1` | Boot-Partition (SD-Karte)     |

Boot bleibt auf der SD-Karte, Root liegt auf der NVMe.

---

## 2. Kritische Pfade

### Konfiguration

| Pfad                              | Auf Root (NVMe) | Beschreibung                         |
|-----------------------------------|-----------------|--------------------------------------|
| `/etc/pi-installer/config.json`   | ja              | Haupt-Konfiguration                  |
| `/etc/pi-installer/backup.json`   | ja              | Backup-Einstellungen & Schedule      |
| `~/.config/pi-installer/config.json` | ja           | Fallback wenn /etc nicht beschreibbar |

### Boot (auf SD-Karte)

| Pfad                         | Auf Root (NVMe) | Beschreibung          |
|------------------------------|-----------------|------------------------|
| `/boot/firmware/config.txt`  | nein (SD)       | Raspberry Pi Konfiguration |
| `/boot/firmware/cmdline.txt` | nein (SD)       | Kernel-Parameter (root=)  |
| `/boot/ssh`                  | nein (SD)       | SSH beim ersten Boot     |

### Mount-Punkte

| Pfad                      | Beschreibung                         |
|---------------------------|--------------------------------------|
| `/mnt/backups`            | Standard-Backup-Verzeichnis          |
| `/mnt/pi-installer-clone` | Temporärer Mount beim Klonen         |
| `/mnt/pi-installer-usb/`  | USB-Sticks für Backup-Ziele          |
| `/mnt/nas`                | NAS-Freigaben                        |

---

## 3. Sudo-Passwort

**Das Sudo-Passwort wird weder im Browser noch in der Tauri-App gespeichert.**

- **Backend:** Passwort liegt nur im Arbeitsspeicher (`sudo_password_store`)
- **Frontend:** Kein Speichern des Passworts (Sicherheit)
- **Verlust:** Bei Backend-Neustart oder mehreren Uvicorn-Workern ist das Passwort weg
- **Empfehlung:** Bei jeder Session neu eingeben oder „Ohne Prüfung speichern“ nutzen

---

## 4. API-Basis-URL

- **Browser:** Relativer Pfad `/api/...` über Vite-Proxy → `localhost:8000`
- **Tauri:** `http://127.0.0.1:8000` (127.0.0.1 statt localhost für stabiles IPv4)
- **Build:** `VITE_API_BASE=http://127.0.0.1:8000 npm run build`

---

## 5. Pfad-Check

`GET /api/system/paths` liefert die wichtigsten Pfade und deren Existenz:

```json
{
  "status": "success",
  "paths": {
    "config_etc": "/etc/pi-installer/config.json",
    "config_etc_exists": true,
    "boot_firmware": "/boot/firmware",
    "boot_firmware_exists": true,
    "root_mount": "/dev/nvme0n1p1",
    ...
  }
}
```

---

## 6. Nach NVMe-Clone prüfen

```bash
# Root-Device
lsblk
# Root sollte /dev/nvme0n1p1 sein

# Boot bleibt auf SD
ls /boot/firmware/config.txt

# Pfade vorhanden?
ls /etc/pi-installer/
ls /mnt/backups 2>/dev/null || sudo mkdir -p /mnt/backups
```
