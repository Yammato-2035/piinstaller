# DEB-Paket bauen und von GitHub installieren

## Verbreitung über GitHub Releases (mit Hash-Prüfung)

**Sinn:** Nutzer können das .deb von GitHub herunterladen, den SHA256-Hash prüfen und mit einem Befehl installieren – ohne das ganze Repo zu klonen.

- Bei jedem **Release** (Tag z. B. `v1.3.9.0`) baut der Workflow `.github/workflows/release-deb.yml` automatisch das .deb und hängt es am Release an, inkl. Datei **SHA256SUMS**.
- **Installation mit Verifikation:**
  ```bash
  # Beispiel für v1.3.9.0 (URL an gewünschte Version anpassen)
  RELEASE="v1.3.9.0"
  BASE="https://github.com/Yammato-2035/piinstaller/releases/download"
  wget "$BASE/$RELEASE/pi-installer_1.3.9.0-1_all.deb"
  wget "$BASE/$RELEASE/SHA256SUMS"
  sha256sum -c SHA256SUMS
  sudo apt install ./pi-installer_1.3.9.0-1_all.deb
  ```
- Die Hashwerte in **SHA256SUMS** ermöglichen eine Prüfung vor der Installation (Supply-Chain-Sicherheit).

---

## Voraussetzungen (Paket selbst bauen)

```bash
sudo apt install debhelper rsync
```

Falls Sie das Tauri Binary mit einbinden möchten (empfohlen):

```bash
# Rust installieren (falls nicht vorhanden)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Systemabhängigkeiten für Tauri
sudo apt install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

## DEB-Paket bauen

```bash
cd /home/volker/piinstaller
./scripts/build-deb.sh
```

Das Paket wird im übergeordneten Verzeichnis erstellt: `../pi-installer_1.3.4.5-1_all.deb`

## Installation

```bash
sudo cp ../pi-installer_1.3.4.5-1_all.deb /tmp/
sudo apt install /tmp/pi-installer_1.3.4.5-1_all.deb
```

## Update

```bash
sudo apt install --only-upgrade /tmp/pi-installer_1.3.4.5-1_all.deb
```

## Release-Workflow (für Betreiber)

1. Version in `config/version.json` anpassen und `frontend/sync-version.js` ausführen.
2. Commit, Push, dann auf GitHub ein **Release** erstellen (Tag z. B. `v1.3.9.0`).
3. Nach dem Veröffentlichen des Releases baut der Workflow **Release .deb** das Paket und fügt dem Release die Dateien **pi-installer_&lt;version&gt;-1_all.deb** und **SHA256SUMS** hinzu.
4. Nutzer können das .deb von der Release-Seite herunterladen und wie oben mit Hash-Prüfung installieren.
