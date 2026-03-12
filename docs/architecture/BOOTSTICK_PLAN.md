^+PI-Installer - Bootstick & Custom Image Plan

**Erstellt:** 2026-01-27  
**Status:** In Planung  
**Ziel:** Eigenes Raspberry Pi OS Image mit vorinstalliertem PI-Installer

---

## 🎯 Zielsetzung

Ein **eigenes Raspberry Pi OS Image** erstellen, das:
- ✅ PI-Installer bereits vorinstalliert hat
- ✅ Beim ersten Boot automatisch startet
- ✅ Auf einem USB-Stick gebootet werden kann
- ✅ Einfach auf SD-Karten geflasht werden kann
- ✅ Minimal konfiguriert ist (keine unnötigen Pakete)

---

## 📋 Phase 1: Basis-Setup (Woche 1-2)

### 1.1 Raspberry Pi OS Image vorbereiten
- [ ] **Raspberry Pi OS Lite** herunterladen (Debian Bookworm)
- [ ] Image auf SD-Karte flashen
- [ ] Basis-Konfiguration durchführen:
  - SSH aktivieren
  - WLAN konfigurieren (optional)
  - Benutzer einrichten
  - System aktualisieren

### 1.2 PI-Installer Installation automatisieren
- [ ] **Installations-Script erstellen** (`/usr/local/bin/pi-installer-setup.sh`)
  - Git Repository klonen
  - Python-Abhängigkeiten installieren
  - Node.js installieren (für Frontend)
  - Systemd-Service erstellen
  - Nginx-Konfiguration einrichten
  - Automatischer Start beim Boot

### 1.3 Systemd Service erstellen
- [ ] **Service-Datei** (`/etc/systemd/system/pi-installer.service`)
  - Startet Backend automatisch
  - Startet Frontend automatisch
  - Automatischer Neustart bei Fehlern
  - Abhängigkeiten definieren (Netzwerk, etc.)

### 1.4 Nginx Reverse Proxy konfigurieren
- [ ] **Nginx-Konfiguration** (`/etc/nginx/sites-available/pi-installer`)
  - Reverse Proxy für Backend (Port 8000)
  - Frontend-Serving (Port 3000 oder statisch)
  - SSL/TLS vorbereiten (später)
  - Automatische Aktivierung

---

## 📋 Phase 2: Image-Optimierung (Woche 2-3)

### 2.1 System-Bereinigung
- [ ] **Unnötige Pakete entfernen**
  - Unused packages
  - Development tools (optional)
  - Dokumentation (optional)
  - Locale-Daten reduzieren

### 2.2 Boot-Optimierung
- [ ] **Boot-Zeit optimieren**
  - Unnötige Services deaktivieren
  - Boot-Reihenfolge optimieren
  - Systemd-Targets optimieren

### 2.3 Speicher-Optimierung
- [ ] **Image-Größe reduzieren**
  - Logs bereinigen
  - Cache leeren
  - Temporäre Dateien entfernen
  - APT-Cache leeren

### 2.4 Sicherheit
- [ ] **Standard-Passwörter ändern**
  - Root-Passwort setzen
  - Standard-Benutzer-Passwort ändern
  - SSH-Keys generieren (optional)

---

## 📋 Phase 3: Automatisierung (Woche 3-4)

### 3.1 First-Boot-Script
- [ ] **Erstes Boot-Script** (`/usr/local/bin/pi-installer-firstboot.sh`)
  - Prüft ob bereits konfiguriert
  - Zeigt Willkommens-Nachricht
  - Startet PI-Installer Web-Interface
  - Erstellt Admin-Benutzer (optional)

### 3.2 Image-Erstellung automatisieren
- [ ] **Build-Script erstellen** (`scripts/build-image.sh`)
  - Image herunterladen
  - Image mounten
  - Änderungen anwenden
  - Image erstellen
  - Komprimierung

### 3.3 CI/CD Integration
- [ ] **GitHub Actions Workflow**
  - Automatischer Build bei Release
  - Image-Upload zu Releases
  - Checksummen generieren
  - Dokumentation aktualisieren

---

## 📋 Phase 4: USB-Boot Support (Woche 4-5)

### 4.1 USB-Boot aktivieren
- [ ] **USB-Boot konfigurieren**
  - Bootloader aktualisieren
  - USB-Storage-Support aktivieren
  - Boot-Reihenfolge konfigurieren

### 4.2 USB-Stick Image erstellen
- [ ] **USB-optimiertes Image**
  - Größere Partitionen
  - Optimierte Mount-Optionen
  - USB-spezifische Konfiguration

### 4.3 Bootstick-Erstellung automatisieren
- [ ] **Script für Bootstick** (`scripts/create-bootstick.sh`)
  - USB-Stick formatieren
  - Image auf USB-Stick kopieren
  - Bootloader installieren
  - Verifizierung

---

## 📋 Phase 5: Dokumentation & Testing (Woche 5-6)

### 5.1 Dokumentation
- [ ] **Installations-Anleitung**
  - Image herunterladen
  - Auf SD-Karte flashen
  - Ersten Boot durchführen
  - Zugriff auf Web-Interface

### 5.2 Testing
- [ ] **Verschiedene Hardware testen**
  - Raspberry Pi 4
  - Raspberry Pi 5
  - Raspberry Pi Zero 2 W
  - Verschiedene SD-Karten

### 5.3 Release-Vorbereitung
- [ ] **Release-Paket erstellen**
  - Image-Datei
  - Checksummen
  - Installations-Anleitung
  - Changelog

---

## 🛠️ Technische Details

### Image-Struktur
```
/boot/firmware/
  ├── config.txt          # Raspberry Pi Konfiguration
  ├── cmdline.txt         # Kernel-Parameter
  └── ...

/etc/systemd/system/
  ├── pi-installer.service
  └── pi-installer-firstboot.service

/usr/local/bin/
  ├── pi-installer-setup.sh
  └── pi-installer-firstboot.sh

/opt/pi-installer/
  ├── backend/
  ├── frontend/
  └── ...
```

### Systemd Service Beispiel
```ini
[Unit]
Description=PI-Installer Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/pi-installer
ExecStart=/usr/bin/python3 /opt/pi-installer/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### First-Boot Script Beispiel
```bash
#!/bin/bash
FIRSTBOOT_FLAG="/etc/pi-installer/.firstboot-done"

if [ -f "$FIRSTBOOT_FLAG" ]; then
    exit 0
fi

# Erste Konfiguration durchführen
echo "PI-Installer wird initialisiert..."

# Service starten
systemctl enable pi-installer
systemctl start pi-installer

# Flag setzen
touch "$FIRSTBOOT_FLAG"
```

---

## 📦 Build-Tools

### Benötigte Tools
- `qemu-user-static` - Für chroot in Image
- `parted` - Partition-Management
- `kpartx` - Loop-Device-Management
- `rsync` - Datei-Synchronisation
- `zip` - Komprimierung

### Build-Script Struktur
```bash
#!/bin/bash
# scripts/build-image.sh

IMAGE_URL="https://downloads.raspberrypi.org/..."
OUTPUT_DIR="./build"
IMAGE_NAME="pi-installer-$(date +%Y%m%d).img"

# 1. Image herunterladen
# 2. Image mounten
# 3. Änderungen anwenden
# 4. Image erstellen
# 5. Komprimieren
```

---

## 🔄 Release-Prozess

### Versionierung
- **Format:** `v1.0.0-image-YYYYMMDD`
- **Beispiel:** `v1.0.0-image-20260127`

### Release-Checkliste
- [ ] Image gebaut und getestet
- [ ] Dokumentation aktualisiert
- [ ] Changelog erstellt
- [ ] Checksummen generiert
- [ ] GitHub Release erstellt
- [ ] Download-Links geprüft

---

## 🎯 Nächste Schritte

### Sofort (Diese Woche)
1. **Basis-Setup-Script erstellen**
   - `/usr/local/bin/pi-installer-setup.sh`
   - Automatische Installation aller Abhängigkeiten
   - Service-Konfiguration

2. **Systemd Service erstellen**
   - `/etc/systemd/system/pi-installer.service`
   - Automatischer Start beim Boot

3. **Nginx-Konfiguration**
   - Reverse Proxy Setup
   - Frontend-Serving

### Diese Woche (Priorität 2)
4. **First-Boot-Script**
   - Automatische Initialisierung
   - Willkommens-Nachricht

5. **Build-Script erstellen**
   - Image-Erstellung automatisieren
   - Testing

### Nächste Woche (Priorität 3)
6. **USB-Boot Support**
   - Bootloader aktualisieren
   - USB-Stick Image

7. **Dokumentation**
   - Installations-Anleitung
   - Troubleshooting

---

## 📊 Fortschritts-Tracking

### In Arbeit
- 🔄 Basis-Setup-Script
- 🔄 Systemd Service
- 🔄 Nginx-Konfiguration

### Geplant
- ⏳ First-Boot-Script
- ⏳ Build-Script
- ⏳ USB-Boot Support
- ⏳ Dokumentation

---

## 🔗 Ressourcen

- [Raspberry Pi OS Images](https://www.raspberrypi.org/downloads/)
- [Raspberry Pi USB Boot](https://www.raspberrypi.org/documentation/hardware/raspberrypi/bootmodes/msd.md)
- [Systemd Service](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Nginx Reverse Proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

---

**Letzte Aktualisierung:** 2026-01-27
