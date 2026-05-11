# Setuphelfer Website Umsetzungstatus (2026-03-20)

## Phasenstand (in Reihenfolge)

1. **Phase 1 – Bestandsaufnahme und Asset-Audit:** abgeschlossen (Assets, Tutorials, Backend-Endpunkte geprueft)
2. **Phase 2 – Branding-System festziehen:** abgeschlossen (Rollen fuer Hauptlogo, Wortmarke, Signet, Favicon, App-Icon definiert)
3. **Phase 3 – Hero Section produktnah:** abgeschlossen (klare Produktaussage + CTA-Hierarchie + produktnahe Hero-Grafik)
4. **Phase 4 – Build-Screenshots:** abgeschlossen mit echten Build-Screenshots im Repo und Einbindung in zentrale Website-Bereiche
5. **Phase 5 – Tutorials integrieren:** abgeschlossen (Bestand erweitert, Ueberlappungen bewertet)
6. **Phase 6 – Live-Daten-Anbindung:** aktualisiert und technisch gehaertet (Healthcheck + kombinierte Endpunkte)
7. **Phase 7 – Farbsystem app-naeher:** abgeschlossen
8. **Phase 8 – Abschlusspruefung:** aktualisiert durch technische Nachschaerfung in Phase 6

## Verbindliche Dokumentation der Umsetzung

- **Welche Logoversion wurde gewaehlt und warum?**
  - Hauptlogo: `assets/branding/setuphelfer-logo-main.svg`
  - Kompakte Wortmarke: `assets/branding/setuphelfer-wordmark-compact.svg`
  - Signet: `assets/branding/setuphelfer-signet.svg`
  - Favicon: `assets/branding/setuphelfer-favicon.svg`
  - App-nahes Icon: `assets/branding/setuphelfer-app-icon.svg`
  - Grund: bestehende, bereits passende Entwuerfe wurden verbindlich auf Rollen verteilt statt neu erfunden.

- **Welche Hero-Grafiken wurden verwendet oder ersetzt?**
  - Aktive Hero-Grafik: `assets/hero/hero-setup-scene.svg`
  - Rolle: visuelle Produktverbindung zwischen Tux, Raspberry Pi, Laptop/Desktop und Setup-Kontext.
  - Keine Comic-Neuinterpretation, keine Stockgrafiken.

- **Welche Screenshots aus dem Build wurden eingebunden?**
  - Eingebunden auf Startseite (`snippets/index.html`):
    - `screenshot-dashboard.png`
    - `screenshot-wizard.png`
    - `screenshot-settings.png`
  - Eingebunden auf Download-Seite (`snippets/download.html`):
    - `screenshot-dashboard.png`
    - `screenshot-presets.png`
    - `screenshot-security.png`
    - `screenshot-users.png`
    - `screenshot-backup.png`
    - `screenshot-documentation.png`
  - Eingebunden in Tutorials:
    - `tutorial-first-setup.html` (Wizard, Dashboard, Settings)
    - `tutorial-network-basics.html` (Dashboard, Monitoring, Webserver)
    - `tutorial-linux-basics.html` (Dashboard, Users, Settings)
    - `tutorial-docker-basics.html` (Dev-Umgebung, Webserver, NAS)
    - `tutorial-backup-basics.html` (Backup, Control Center, Dokumentation)

- **Welche Tutorials wurden zusaetzlich integriert?**
  - Vertiefungen: `tutorial-network-basics`, `tutorial-backup-basics`, `tutorial-linux-basics`
  - Hauptpfad-Tutorials (Install/WLAN/SSH/Backup/Updates/Docker/NVMe) bleiben erhalten.

- **Welche Backend-Endpunkte wurden gefunden?**
  - `GET /health`
  - `GET /api/status`
  - `GET /api/system-info?light=1`
  - `GET /api/system/network`
  - weitere systemnahe Endpunkte vorhanden (z. B. `/api/system/resources`)

- **Wie funktioniert die Live-Daten-Anzeige?**
  - Erst Healthcheck (`/health`), danach Polling alle 10 Sekunden.
  - Datenquellen kombiniert:
    - Systemwerte aus `/api/system-info?light=1`
    - Host/Status aus `/api/status` und `/api/system/network`
  - Anzeige: CPU, RAM, Speicher, Hostname, Betriebssystem, Netzwerk, Uptime, Installationsstatus, letzte Aktualisierung.

- **Welche Fallbacks gibt es, wenn das Backend nicht laeuft?**
  - Sichtbare Statuszustaende: `Ladezustand`, `Backend verbunden`, `Setuphelfer laeuft lokal`, `Backend nicht erreichbar`
  - Bei Fehlern werden Werte auf `-` gesetzt, keine Fantasiedaten.
  - Wenn nur Teilendpunkte antworten, werden verfuegbare Daten angezeigt, fehlende Felder bleiben neutral.

- **Welche Farb- und Icon-Anpassungen wurden vorgenommen?**
  - Farbvariablen und CTA-Akzente app-naeher ausgerichtet (Sky/Petrol, weiterhin ruhig/professionell).
  - Icon-Nutzung in Kernbereichen wurde auf konsistente SVG-Sets aus dem Theme ausgerichtet; verbleibende Alt-Assets sind fuer gezielten Folge-Cleanup markiert.
