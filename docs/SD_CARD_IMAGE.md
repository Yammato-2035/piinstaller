# SD-Card-Image (Phase 1.2 – Transformationsplan)

Ziel: Eine **.img-Datei** zum direkten Flashen auf eine SD-Karte (ähnlich wie Home Assistant OS), mit PI-Installer vorinstalliert und beim ersten Boot startbereit.

## Optionen

### Option A: GitHub Actions Overlay-Artefakt

Der Workflow **.github/workflows/build-image.yml** erstellt bei Push (oder manuell) ein Artefakt **pi-installer-overlay**: ein Tarball mit

- `scripts/create_installer.sh`
- `pi-installer.service`
- `start.sh`
- `backend/`, `frontend/`, `VERSION`

Dieses Overlay kann in ein bestehendes Raspberry Pi OS (Lite) Image eingebunden werden (z. B. in einer zweiten Pipeline oder manuell mit chroot/pi-gen).

### Option B: Manuelles Image mit Raspberry Pi OS Lite

1. **Raspberry Pi OS Lite** von [raspberrypi.com](https://www.raspberrypi.com/software/) herunterladen und mit Raspberry Pi Imager auf SD-Karte flashen.
2. **Ersten Boot vorbereiten:** Vor dem ersten Start die SD-Karte mounten und z. B. eine leere Datei `ssh` im Boot-Partition anlegen (für SSH-Zugang).
3. **Nach dem ersten Boot:** Per SSH verbinden und den **One-Click-Installer** ausführen:
   ```bash
   curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh | bash
   ```
   oder mit Repo-URL:
   ```bash
   PI_INSTALLER_REPO=https://github.com/Yammato-2035/piinstaller.git bash -c "$(curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh)"
   ```
4. Danach: Browser öffnen mit der angezeigten URL (z. B. `http://<IP>:3001`).

### Option C: Eigenes Image mit pi-gen

[pi-gen](https://github.com/RPi-Distro/pi-gen) ist das offizielle Tool zum Erstellen von Raspberry Pi OS Images. Um PI-Installer vorzuinstallieren:

1. **pi-gen** klonen und Stage anlegen (z. B. `stage-pi-installer`).
2. In der Stage: Repository klonen, Dependencies installieren (Python, Node), systemd-Service einrichten.
3. Image bauen; die ausgegebene .img auf SD-Karte flashen.
4. **Erster Boot:** Optional First-Run-Wizard für WLAN/Netzwerk (kann über PI-Installer-Weboberfläche oder ein kleines Skript im Image erfolgen).

Die genaue Stage-Konfiguration (Skripte, Pakete) ist projektspezifisch und kann bei Bedarf in diesem Repo unter `scripts/pi-gen-stage/` oder in einer separaten Dokumentation beschrieben werden.

### Option D: WLAN/Netzwerk beim ersten Boot

Damit das geflashte Image ohne Monitor nutzbar ist:

- **Raspberry Pi Imager** bietet unter „Einstellungen“ (Zahnrad) die Option, WLAN und SSH beim ersten Start zu konfigurieren.
- Oder manuell: Auf der Boot-Partition `wpa_supplicant.conf` und leere Datei `ssh` anlegen (siehe Raspberry Pi Dokumentation).

## Zusammenfassung

| Methode              | Aufwand | Ergebnis                                      |
|----------------------|---------|-----------------------------------------------|
| One-Click nach Flash | Gering  | Nutzer flasht Pi OS Lite, führt dann 1 Befehl aus |
| Overlay + eigener Build | Mittel | Tarball aus GitHub Actions in eigenes Image einbauen |
| pi-gen Stage         | Hoch    | Vollständiges .img mit PI-Installer vorinstalliert |

Für die meisten Nutzer reicht **Option B** (Pi OS Lite flashen, dann One-Click-Installer). Option C ist für ein „echtes“ All-in-One-Image wie bei Home Assistant OS gedacht.

## Siehe auch

- **scripts/create_installer.sh** – One-Click-Installer
- **docs/GET_PI_INSTALLER_IO.md** – One-Liner-URL
- **TRANSFORMATIONSPLAN.md** – Phase 1.2 SD-Card Image
