# PI-Installer als Debian-Paket (apt)

PI-Installer kann als `.deb`-Paket gebaut und über den Paketmanager installiert bzw. aktualisiert werden.

## Paket bauen

### Voraussetzungen

```bash
sudo apt install debhelper rsync
```

### Build ausführen

Im Repository-Root:

```bash
./scripts/build-deb.sh
```

Das Paket liegt danach im übergeordneten Verzeichnis, z. B. `../pi-installer_1.3.4.2-1_all.deb`.

### Version anpassen

Vor dem Build die Version in **`debian/changelog`** anpassen (erste Zeile):

```
pi-installer (1.3.4.2-1) unstable; urgency=medium
```

Dabei `1.3.4.2` durch die gewünschte Version ersetzen; `-1` ist die Paketrevision.

## Installation

### Einmalige Installation der .deb

**Hinweis:** Liegt die .deb in deinem Home (z. B. `~/pi-installer_*.deb`), kann apt sie nicht lesen (Benutzer `_apt` hat keinen Zugriff). Dann zuerst nach `/tmp` kopieren:

```bash
sudo cp /pfad/zur/pi-installer_1.3.4.2-1_all.deb /tmp/
sudo apt install /tmp/pi-installer_1.3.4.2-1_all.deb
```

Wenn die .deb im aktuellen Verzeichnis liegt (z. B. nach dem Build im Repo-Root):

```bash
sudo cp ./pi-installer_1.3.4.2-1_all.deb /tmp/
sudo apt install /tmp/pi-installer_1.3.4.2-1_all.deb
```

Oder von einer heruntergeladenen Datei (z. B. von GitHub Releases) – bei Dateien in `~/Downloads` ebenfalls über `/tmp` installieren.

### Update über apt

Wenn Sie ein Repository mit PI-Installer-Paketen eingerichtet haben:

```bash
sudo apt update
sudo apt install --only-upgrade pi-installer
```

Ohne Repository: neue .deb von GitHub Releases herunterladen und erneut `sudo apt install ./pi-installer_*.deb` ausführen (ersetzt die alte Version).

## Was das Paket macht

- Installiert alle Dateien nach **/opt/pi-installer**
- **Bindet das Tauri Binary ein** (falls beim Build erstellt)
- Legt den Service-Benutzer **pi-installer** an
- Konfiguration: **/etc/pi-installer**, Logs: **/var/log/pi-installer**
- Richtet **systemd-Service** `pi-installer.service` ein (startet beim Booten)
- Legt **Startmenü-Einträge** an (PI-Installer, PI-Installer im Browser)
- Beim ersten Install/Update: Backend-Venv und Frontend-`npm install` werden automatisch ausgeführt
- Falls Tauri Binary fehlt: Versucht es während der Installation zu bauen (nur wenn `cargo` verfügbar)

## Paket für GitHub Releases bereitstellen

1. **Version setzen:** `VERSION` und erste Zeile in `debian/changelog` anpassen.
2. **.deb bauen:** `./scripts/build-deb.sh`
3. **Auf GitHub:** Neues Release anlegen (Tag z. B. `v1.3.4.2`), die Datei `pi-installer_1.3.4.2-1_all.deb` aus dem übergeordneten Verzeichnis als Asset hochladen.
4. Nutzer können die .deb herunterladen und mit `sudo apt install ./pi-installer_*.deb` installieren bzw. updaten.

## Eigenes apt-Repository (optional)

Für automatische Updates per `apt upgrade` können Sie ein kleines apt-Repository hosten (z. B. auf GitHub Pages oder einem eigenen Server) und die .deb-Dateien dort ablegen. Dafür sind zusätzlich `reprepro` oder `apt-ftparchive` und eine Konfiguration nötig – siehe Debian-Dokumentation zu „Repository erstellen“.
