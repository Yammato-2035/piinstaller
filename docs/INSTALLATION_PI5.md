# PI-Installer auf Raspberry Pi 5 installieren

Diese Anleitung zeigt, wie Sie PI-Installer auf einem **neu installierten Raspberry Pi 5** installieren.

## Voraussetzungen

- Raspberry Pi 5 mit Raspberry Pi OS (Debian-basiert)
- Internetverbindung
- SSH-Zugriff oder direkter Zugriff auf den Pi
- Root/Sudo-Zugriff

## Schnellstart – Ein Befehl

### Option 1: Systemweite Installation (empfohlen)

Installiert PI-Installer nach `/opt/pi-installer/` gemäß Linux-Standards:

```bash
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash
```

**Nach der Installation:**
- Globale Befehle verfügbar: `pi-installer`, `pi-installer-backend`, etc.
- Web-Interface: http://localhost:3001
- Service startet automatisch beim Booten

### Option 2: Benutzer-Installation (für Entwicklung/Test)

Installiert PI-Installer nach `$HOME/PI-Installer/`:

```bash
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh | bash
```

**Nach der Installation:**
- Programm in `~/PI-Installer/`
- Starten mit: `cd ~/PI-Installer && ./start.sh`

### Option 3: Interaktive Auswahl

Wählen Sie zwischen beiden Optionen:

```bash
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install.sh | bash
```

---

## Schritt-für-Schritt Anleitung

### Schritt 1: Raspberry Pi OS installieren

1. **Raspberry Pi OS herunterladen**
   - Von: https://www.raspberrypi.com/software/
   - Raspberry Pi OS (64-bit) empfohlen

2. **Auf SD-Karte flashen**
   - Mit Raspberry Pi Imager oder ähnlichem Tool
   - **Wichtig:** SSH aktivieren (für Remote-Zugriff)
     - Im Imager: ⚙️ → "Enable SSH" → Passwort setzen

3. **SD-Karte in Pi 5 einstecken und starten**

### Schritt 2: Mit dem Pi verbinden

#### Option A: Direkt am Pi (Monitor + Tastatur)
- Einfach einloggen und Terminal öffnen

#### Option B: Per SSH (empfohlen)
```bash
# Von Ihrem Computer aus:
ssh pi@<PI-IP-ADRESSE>
# Beispiel: ssh pi@192.168.1.100
```

**IP-Adresse finden:**
- Im Router-Dashboard
- Oder am Pi: `hostname -I`

### Schritt 3: PI-Installer installieren

#### Systemweite Installation (empfohlen)

```bash
# Ein Befehl – alles wird automatisch installiert
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash
```

**Was passiert:**
1. ✅ System-Abhängigkeiten werden installiert (Python, Node.js, Git, etc.)
2. ✅ Repository wird geklont nach `/opt/pi-installer/`
3. ✅ Backend-Dependencies werden installiert
4. ✅ Frontend-Dependencies werden installiert
5. ✅ Konfiguration wird erstellt (`/etc/pi-installer/`)
6. ✅ Symlinks werden erstellt (`/usr/local/bin/`)
7. ✅ Umgebungsvariablen werden gesetzt
8. ✅ systemd Service wird eingerichtet

**Nach der Installation:**
- Service startet automatisch (falls gewählt)
- Zugriff über: http://localhost:3001 oder http://<PI-IP>:3001

#### Benutzer-Installation (Alternative)

```bash
# Keine Root-Rechte nötig
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh | bash
```

**Nach der Installation:**
```bash
cd ~/PI-Installer
./start.sh
```

### Schritt 4: Zugriff auf PI-Installer

#### Lokal am Pi
Öffnen Sie im Browser:
```
http://localhost:3001
```

#### Von anderem Gerät im Netzwerk
Öffnen Sie im Browser:
```
http://<PI-IP-ADRESSE>:3001
```

**IP-Adresse finden:**
```bash
hostname -I
```

### Schritt 5: Erste Schritte

1. **Erste-Schritte-Assistent** wird automatisch angezeigt
2. **System konfigurieren:**
   - Benutzer erstellen
   - Sicherheitseinstellungen
   - Netzwerk konfigurieren
3. **Apps installieren** aus dem App Store

---

## Was wird installiert?

### System-Abhängigkeiten
- Python 3.9+ (mit venv und pip)
- Node.js und npm
- Git, curl, wget, build-essential

### PI-Installer
- Backend (FastAPI) auf Port 8000
- Frontend (React/Vite) auf Port 3001
- Alle benötigten Python- und Node-Pakete

### Verzeichnisse (bei systemweiter Installation)
- `/opt/pi-installer/` – Programmdateien
- `/etc/pi-installer/` – Konfiguration
- `/var/log/pi-installer/` – Logs

---

## Verfügbare Befehle (nach systemweiter Installation)

```bash
# Hauptbefehl (startet Backend + Frontend)
pi-installer

# Nur Backend
pi-installer-backend

# Nur Frontend
pi-installer-frontend

# Service-Verwaltung
sudo systemctl status pi-installer
sudo systemctl start pi-installer
sudo systemctl stop pi-installer
sudo systemctl restart pi-installer
```

---

## Troubleshooting

### Installation schlägt fehl

**Problem:** Python oder Node.js nicht gefunden
```bash
# Manuell installieren:
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git
```

**Problem:** Keine Internetverbindung
```bash
# Prüfen:
ping -c 3 8.8.8.8

# Falls WLAN nicht verbunden:
sudo raspi-config
# → System Options → Wireless LAN
```

### Service startet nicht

```bash
# Status prüfen:
sudo systemctl status pi-installer

# Logs anzeigen:
sudo journalctl -u pi-installer -n 50

# Manuell starten:
sudo systemctl start pi-installer
```

### Port bereits belegt

```bash
# Prüfen welche Prozesse Port 8000/3001 nutzen:
sudo lsof -i :8000
sudo lsof -i :3001

# Falls nötig, Prozess beenden:
sudo kill <PID>
```

### Zugriff von außen nicht möglich

```bash
# Firewall prüfen:
sudo ufw status

# Falls aktiviert, Ports öffnen:
sudo ufw allow 3001/tcp
sudo ufw allow 8000/tcp
```

---

## Weitere Informationen

- **[SYSTEM_INSTALLATION.md](SYSTEM_INSTALLATION.md)** – Detaillierte Anleitung zur systemweiten Installation
- **[INSTALL.md](../../INSTALL.md)** – Vollständige Installationsanleitung
- **[QUICKSTART.md](../../QUICKSTART.md)** – Schnellstart-Anleitung
- **[README.md](../../README.md)** – Projekt-Übersicht

---

## Häufige Fragen

**F: Welche Python-Version wird benötigt?**  
A: Python 3.9 oder höher (wird automatisch installiert)

**F: Wie lange dauert die Installation?**  
A: Ca. 5-15 Minuten, abhängig von Internetgeschwindigkeit

**F: Kann ich PI-Installer auch ohne Internet installieren?**  
A: Nein, Internetverbindung ist für Package-Downloads erforderlich

**F: Funktioniert das auch auf Pi 4?**  
A: Ja, funktioniert auf Raspberry Pi 4 und neuer

**F: Wie aktualisiere ich PI-Installer?**  
A: Bei systemweiter Installation: `sudo /opt/pi-installer/scripts/update-system.sh`
