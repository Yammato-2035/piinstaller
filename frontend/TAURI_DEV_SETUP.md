# Tauri-Desktop-App lokal starten

Die PI-Installer-Desktop-App (Tauri) benötigt **Rust** und unter Linux zusätzlich Systempakete.

## Fehler: „failed to parse config: package > version must be a semver string“

Die Version in `src-tauri/tauri.conf.json` muss **SemVer** sein (nur drei Teile: z. B. `1.3.5`, nicht `1.3.4.2`). Bei diesem Fehler die Version in der Config anpassen.

## Fehler: „failed to run 'cargo metadata'“

Bedeutet: **Rust/Cargo ist nicht installiert** oder nicht im PATH.

## 1. Rust installieren

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Option **1** (Standard-Installation) wählen. Anschließend Terminal neu starten oder:

```bash
source "$HOME/.cargo/env"
```

Prüfen: `cargo --version` und `rustc --version` sollten etwas ausgeben.

## 2. Systemabhängigkeiten (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

Andere Distributionen: [Tauri – Prerequisites (Linux)](https://v2.tauri.app/start/prerequisites).

## 3. Tauri-App starten

```bash
cd frontend
npm install
npm run tauri:dev
```

Beim ersten Mal baut Cargo die native Komponente (kann einige Minuten dauern).

## App startet nicht / Build-Fehler (permissions, No such file)

- **Projektpfad ohne Leerzeichen** wählen (z. B. `~/piinstaller` statt `~/Dokumente/Software aus PI holen/piinstaller`), dann erneut starten.
- **Build-Cache leeren** und neu bauen:
  ```bash
  cd frontend
  rm -rf src-tauri/target
  npm run tauri:dev
  ```

## Nur Web (ohne Tauri)

Wenn Sie nur das Web-Frontend nutzen wollen (z. B. im Browser oder auf dem Pi):

```bash
npm run dev
```

Dann im Browser: http://localhost:3001
