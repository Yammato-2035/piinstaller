# DEB-Paket bauen - Anleitung

## Voraussetzungen

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
