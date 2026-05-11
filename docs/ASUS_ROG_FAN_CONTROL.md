# ASUS ROG Lüftersteuerung unter Linux

**APT / totes Repo / Docker auf Linux Mint:** siehe die interne Wissensdatenbank [APT_REPOSITORIEN_UND_DOCKER_FAQ.md](knowledge-base/APT_REPOSITORIEN_UND_DOCKER_FAQ.md) (u. a. `repo.asus-linux.org`, Grafana-Keyring, Docker `noble` statt Mint-Codename).

## Übersicht

ASUS ROG Laptops haben spezielle Hardware für die Lüftersteuerung, die unter Windows über die Zusatztasten (Fn+F5) gesteuert werden kann. Unter Linux funktioniert dies standardmäßig nicht, aber mit `asusctl` kann die Lüftersteuerung aktiviert werden.

## Installation

### Schritt 1: asusctl installieren

Führen Sie das Installations-Script aus:

```bash
sudo bash scripts/install-asusctl.sh
```

Das Script:
- Erkennt automatisch Ihre Linux-Distribution (Debian/Ubuntu, Fedora/RHEL, Arch)
- Fügt das asus-linux Repository hinzu (bei Debian/Ubuntu)
- Installiert `asusctl` und `supergfxctl`
- Startet den `asusd` Service automatisch

### Schritt 2: Installation prüfen

Prüfen Sie ob alles funktioniert:

```bash
# Prüfe ob asusctl verfügbar ist
asusctl --help

# Prüfe ob asusd Service läuft
systemctl status asusd

# Zeige verfügbare Lüfter-Profile
asusctl fan-curve -p
```

## Verwendung

### Über die Kommandozeile

#### Lüfter-Profil aktivieren

```bash
# Performance-Profil (höchste Lüftergeschwindigkeit)
bash scripts/asus-rog-fan-control.sh Performance

# Balanced-Profil (ausgewogen)
bash scripts/asus-rog-fan-control.sh Balanced

# Quiet-Profil (leiser, niedrigere Geschwindigkeit)
bash scripts/asus-rog-fan-control.sh Quiet
```

#### Status anzeigen

```bash
bash scripts/asus-rog-fan-control.sh status
```

### Über die Web-API

Die PI-Installer Web-GUI bietet API-Endpunkte für die Lüftersteuerung:

#### System-Erkennung

```bash
GET /api/system/asus-rog/detection
```

Antwort:
```json
{
  "is_asus_rog": true,
  "asusctl_available": true,
  "can_control_fans": true
}
```

#### Verfügbare Profile abrufen

```bash
GET /api/system/asus-rog/fan/profiles
```

Antwort:
```json
{
  "available": true,
  "profiles": ["Performance", "Balanced", "Quiet"],
  "error": null
}
```

#### Aktuellen Status abrufen

```bash
GET /api/system/asus-rog/fan/status
```

Antwort:
```json
{
  "available": true,
  "service_running": true,
  "curves": "...",
  "error": null
}
```

#### Profil setzen

```bash
POST /api/system/asus-rog/fan/set-profile
Content-Type: application/json

{
  "profile": "Performance"
}
```

Antwort:
```json
{
  "success": true,
  "profile": "Performance",
  "error": null
}
```

### Direkt mit asusctl

```bash
# Verfügbare Profile anzeigen
asusctl profile list

# Aktuelles Profil anzeigen
asusctl profile get

# Profil setzen
sudo asusctl profile set Performance
sudo asusctl profile set Balanced
sudo asusctl profile set Quiet

# Aktuelle Lüfter-Kurven-Status anzeigen
asusctl fan-curve --get-enabled

# Lüfter-Kurven für ein Profil anzeigen
asusctl fan-curve --mod-profile Performance
asusctl fan-curve --mod-profile Balanced
asusctl fan-curve --mod-profile Quiet

# Lüfter-Kurven für ein Profil aktivieren
sudo asusctl fan-curve --mod-profile Performance --enable-fan-curves true
sudo asusctl fan-curve --mod-profile Balanced --enable-fan-curves true
sudo asusctl fan-curve --mod-profile Quiet --enable-fan-curves true

# System-Informationen
asusctl info
```

## Verfügbare Profile

### Performance
- **Beschreibung**: Höchste Lüftergeschwindigkeit für maximale Kühlung
- **Verwendung**: Bei intensiven Aufgaben wie Gaming, Video-Rendering, etc.
- **Nachteil**: Lauter, höherer Stromverbrauch
- **Aktivierung**: `sudo asusctl profile set Performance`

### Balanced
- **Beschreibung**: Ausgewogenes Profil zwischen Leistung und Lautstärke
- **Verwendung**: Für normale bis hohe Lasten
- **Nachteil**: Keine
- **Aktivierung**: `sudo asusctl profile set Balanced`

### Quiet
- **Beschreibung**: Niedrigere Lüftergeschwindigkeit für leiseres Arbeiten
- **Verwendung**: Bei leichten Aufgaben, Büroarbeit, etc.
- **Nachteil**: Kann bei hoher Last zu höheren Temperaturen führen
- **Aktivierung**: `sudo asusctl profile set Quiet`

**Wichtig**: Nach dem Setzen eines Profils sollten Sie auch die Lüfter-Kurven aktivieren:
```bash
sudo asusctl fan-curve --mod-profile Performance --enable-fan-curves true
```

## Benutzerdefinierte Lüfter-Kurven

Sie können auch benutzerdefinierte Lüfter-Kurven erstellen. Die Syntax ist:

```bash
# Format: Temperatur:Prozent
# Beispiel: 30°C = 1%, 40°C = 5%, 50°C = 10%
sudo asusctl fan-curve --mod-profile Performance --fan CPU --data "30c:1%,40c:5%,50c:10%"

# Für GPU
sudo asusctl fan-curve --mod-profile Performance --fan GPU --data "30c:1%,40c:5%,50c:10%"

# Aktivieren der benutzerdefinierten Kurve
sudo asusctl fan-curve --mod-profile Performance --enable-fan-curve true --fan CPU
```

## Troubleshooting

### Repository nicht erreichbar (DNS-Fehler)

Wenn Sie eine Fehlermeldung wie "repo.asus-linux.org konnte nicht aufgelöst werden" erhalten:

1. **Automatische Lösung**: Das Installations-Script erkennt dies automatisch und kompiliert `asusctl` aus dem Quellcode
2. **Manuelle Prüfung**: 
   ```bash
   # Prüfe Netzwerk-Verbindung
   ping -c 3 repo.asus-linux.org
   
   # Prüfe DNS-Auflösung
   nslookup repo.asus-linux.org
   ```
3. **Alternative**: Das Script kompiliert automatisch aus dem Quellcode, wenn das Repository nicht erreichbar ist

### asusctl ist nicht installiert

```bash
# Prüfe ob Installation erfolgreich war
which asusctl

# Falls nicht, installiere manuell (kompiliert automatisch aus Quellcode bei Repository-Problemen)
sudo bash scripts/install-asusctl.sh
```

### Kompilierung schlägt fehl

Falls die Kompilierung aus dem Quellcode fehlschlägt:

1. **Prüfe Rust-Installation**:
   ```bash
   rustc --version
   cargo --version
   ```

2. **Installiere Rust manuell**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source "$HOME/.cargo/env"
   ```

3. **Prüfe Build-Abhängigkeiten**:
   ```bash
   # Debian/Ubuntu
   sudo apt-get install -y build-essential libgtk-3-dev libpango1.0-dev libgdk-pixbuf-2.0-dev libglib2.0-dev cmake libclang-dev libudev-dev libayatana-appindicator3-dev pkg-config
   ```

### asusd Service läuft nicht

```bash
# Starte Service manuell
sudo systemctl start asusd.service

# Aktiviere automatischen Start
sudo systemctl enable asusd.service

# Prüfe Status
systemctl status asusd
```

### Lüfter-Profile werden nicht erkannt

- Stellen Sie sicher, dass Ihr ASUS ROG Laptop unterstützt wird
- Prüfen Sie die Kernel-Version (mindestens 5.17 für Ryzen-Modelle)
- Aktualisieren Sie `asusctl` auf die neueste Version

### Hardware wird nicht erkannt

```bash
# Prüfe ob ASUS ROG System erkannt wird
cat /sys/class/dmi/id/product_name

# Prüfe ob asusctl das System erkennt
asusctl info
```

## Unterstützte Hardware

`asusctl` unterstützt viele ASUS ROG Laptops, insbesondere:
- ROG Zephyrus Serie
- ROG Strix Serie
- ROG Flow Serie
- Viele andere ROG Modelle

Eine vollständige Liste finden Sie auf: https://asus-linux.org/

## Weitere Informationen

- **Offizielle Dokumentation**: https://asus-linux.org/manual/asusctl-manual/
- **GitLab Repository**: https://gitlab.com/asus-linux/asusctl
- **FAQ**: https://asus-linux.org/faq/asusctl/custom-fan-curves/

## Hinweise

- Die Lüftersteuerung erfordert Root-Rechte (sudo)
- Änderungen werden sofort angewendet
- Das ausgewählte Profil bleibt aktiv bis zum Neustart oder manueller Änderung
- Bei einigen Modellen sind benutzerdefinierte Kurven nur für Ryzen-basierte Systeme verfügbar
