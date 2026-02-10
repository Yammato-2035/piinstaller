# Changelog

Alle wichtigen Änderungen am PI-Installer werden hier dokumentiert.  
Details und Versionsschema: [VERSIONING.md](./VERSIONING.md).

---

## [1.3.4.0] – 2026-02

### Systemweite Installation gemäß Linux FHS

- **Neue Installationsmethode:** Systemweite Installation nach `/opt/pi-installer/` gemäß Linux Filesystem Hierarchy Standard (FHS)
- **Installations-Skripte:**
  - `scripts/install-system.sh` – Systemweite Installation nach `/opt/pi-installer/`
  - `scripts/update-system.sh` – Update-Skript für bestehende Installationen
  - `scripts/install.sh` – Wrapper mit interaktiver Auswahl zwischen beiden Methoden
- **Installationsverzeichnisse:**
  - Programm: `/opt/pi-installer/`
  - Konfiguration: `/etc/pi-installer/`
  - Logs: `/var/log/pi-installer/`
  - Symlinks: `/usr/local/bin/` (globale Befehle wie `pi-installer`, `pi-installer-backend`)
- **Umgebungsvariablen:** Automatisch in `/etc/profile.d/pi-installer.sh` gesetzt
- **systemd Service:** Verbesserte Sicherheitseinstellungen (NoNewPrivileges, PrivateTmp, ProtectSystem)
- **Dokumentation:** Neue Dokumentation `docs/SYSTEM_INSTALLATION.md` mit vollständiger Anleitung
- **GitHub-Integration:** Alle Installations-Skripte direkt von GitHub verfügbar über Raw-URLs

### Dual Display X11 – Frühe Konfiguration

- **LightDM Integration:** Verwendet `session-setup-script` für frühe Display-Konfiguration nach Login
- **Position korrekt:** DSI-1 wird zuerst gesetzt (links unten 0x1440), dann HDMI-1-2 (rechts oben 480x0)
- **Keine mehrfachen Umschaltungen:** Atomare Konfiguration in einem xrandr-Befehl
- **Alte Skripte deaktiviert:** Automatische Deaktivierung von `enable-hdmi.sh` und verzögerten Autostart-Skripten
- **Skript:** `scripts/fix-gabriel-dual-display-x11-early.sh` für optimierte frühe Konfiguration

---

## [1.3.3.0] – 2026-02

### Dual Display X11 – stabil ohne ständiges Umschalten

- **Stand:** DSI + HDMI unter X11 läuft jetzt richtig; Position (DSI links unten, HDMI rechts oben), Desktop/Hintergrund auf HDMI (Primary), keine ständige Umschaltung mehr.
- **Maßnahmen:** Atomarer xrandr-Befehl (beide Ausgaben in einem Aufruf); .xprofile setzt Layout nach 8 s und startet ~10 s nach Login PCManFM-Desktop neu (Trigger: Desktop → Primary/HDMI); delayed-Script wendet Layout nach 8 s und 16 s an; optional `fix-desktop-on-hdmi-x11.sh` zum manuellen Neustart des Desktops.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) – Spiegelung, Position, Desktop auf HDMI, Trigger, Beschleunigung (~10 s), FAQ-Verweise.
- **FAQ:** Eintrag „Dual Display X11 (DSI + HDMI) – Desktop auf HDMI, stabil“ ergänzt; bestehender Eintrag zur DSI-Spiegelung beibehalten.

---

## [1.3.2.0] – 2026-02

### Dual Display X11 – DSI-Spiegelung auf HDMI

- **Problem:** Der komplette DSI-1-Desktop wurde oben links auf HDMI-1-2 gespiegelt (nicht nur ein Fenster). Ursache: Pi-KMS/DRM-Treiber legt die HDMI-Scanout-Region nicht korrekt ab Offset (480,0).
- **Maßnahmen in Scripts:** Explizite Framebuffer-Größe `xrandr --fb 3920x2240`; Konfiguration **HDMI vor DSI** (HDMI 480x0, dann DSI 0x1440). Angepasst: `fix-gabriel-dual-display-x11.sh`, `.xprofile`, `.screenlayout`, `apply-dual-display-x11-delayed.sh`, `fix-dsi-position-x11.sh`.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) – Problem, umgesetzte Maßnahmen, optionale config.txt-Workarounds, manuelle Tests.
- **FAQ:** Neuer Eintrag „DSI-Desktop oben links auf HDMI gespiegelt (X11)“ in der App-Dokumentation (Dokumentation → FAQ) und Verweis in docs/VIDEO_TUTORIALS.md.

---

## [1.3.1.0] – 2026-02

### Backup & Restore – Laufwerk klonen & NVMe

- **Laufwerk klonen:** Neue Funktion in Backup & Restore – System von SD-Karte auf NVMe/USB-SSD klonen (Hybrid-Boot: Kernel von SD, Root von NVMe). rsync-basiert, fstab und cmdline.txt werden automatisch angepasst.
- **NVMe-Erkennung:** Ziel-Laufwerke (NVMe, USB, SATA) werden über disk-info API erkannt und im Clone-Tab angezeigt. Modell, Größe und Mount-Status sichtbar.
- **Festgestellte Probleme:** Siehe Dokumentation → FAQ für bekannte Einschränkungen und Lösungswege (z. B. NVMe-Pfade nach Clone, Dualdisplay-Konfiguration, Freenove-Case-Anpassungen).

### DSI-Radio (Freenove TFT – native PyQt6-App)

- **Lautstärke:** Regler steuert den aktiven Kanal (PulseAudio: `pactl set-sink-volume @DEFAULT_SINK@`; Fallback: ALSA amixer Master/PCM). Regler rechts neben Senderbuttons, oberhalb des Seitenumschalters (1/2 ▶), silber umrandet.
- **Radioanzeige:** Logo links (96×96), rechts schwarzer Klavierlack-Rahmen mit leuchtend grüner Anzeige und schwarzer Schrift; Schließen-Button (✕) in der Anzeige; Uhr mit Datum, kompakt.
- **D/A-Umschalter:** Langgestrecktes rotes O mit rundem schwarzem Schieber, D (Digital/LED) und A (Analog); analoge VU-Anzeige mit Skala 0–100 %, rechts roter Bereich, Zeiger begrenzt durch Lautstärke.

### Dokumentation

- **Neue Bereiche:** „Freenove Pro – 4,3″ Touchscreen im Gehäuse“ und „Dualdisplay DSI0 + HDMI1 – Zwei Monitore gleichzeitig“ mit Tips & Tricks.
- **Lernbereich:** Themenblock „Touchscreen am DSI0 Port“ ergänzt.
- **FAQ:** Aus Troubleshooting eine vollständige FAQ mit Fehlername, Beschreibung und Lösungen; funktionales Design mit logischer Farbgebung; FAQ-Eintrag „DSI-Radio: Lautstärke funktioniert nicht“ ergänzt.

---

## [1.3.0.1] – 2026-02

### Backup & Restore

- **Cloud-Backups löschen:** Löschung von Cloud-Backups (WebDAV/Seafile) funktioniert; URL-Konstruktion aus PROPFIND-`href` korrigiert (`base_domain + href`); Debug-Info in Response für Fehlerfälle.
- **USB ↔ Cloud Wechsel:** Beim Wechsel von USB zu Cloud und zurück werden die Backups des zuvor gemounteten USB-Sticks wieder geladen; `loadBackups(dirOverride)` und explizites Setzen von `backupDir` + Aufruf beim USB-Button.
- **Kein Cloud-Upload bei USB-Ziel:** Backups mit Ziel USB-Stick werden nicht mehr zusätzlich in die Cloud hochgeladen; Backend lädt nur noch bei `target` `cloud_only` oder `local_and_cloud`, nicht bei `local`.

---

## [1.3.0.0] – 2026-02

### Transformationsplan: „Raspberry Discovery Box“

- **App Store:** Neue Seite mit 7 Apps (Home Assistant, Nextcloud, Pi-hole, Jellyfin, WordPress, VS Code Server, Node-RED); Kachel-Layout, Suche, Kategorien; Ein-Klick-Installation (API vorbereitet, Implementierung folgt).
- **First-Run-Wizard:** Beim ersten Start: Willkommen → Optional (Netzwerk/Sicherheit/Backup) → „Was möchtest du tun?“ (Smart Home, Cloud, Medien, Entwickeln) → Empfohlene Apps → App Store.
- **Dashboard-Redesign:** Hero „Dein Raspberry Pi läuft!“, großer Status (Alles OK / Aktion benötigt), Ressourcen-Ampel (CPU/RAM/Speicher), Schnellaktionen (Neue App installieren, Backup erstellen, System updaten).
- **Mobile:** Hamburger-Menü auf kleinen Screens; Sidebar als Overlay; touch-freundlich; responsive Padding.
- **Kontextsensitive Hilfe:** HelpTooltip-Komponente (?-Icon) an Dashboard und App Store.
- **Einstellungen:** Option „Erfahrene Einstellungen anzeigen“ (versteckt; blendet Grundlegende Einstellungen und Dokumentations-Screenshots ein).
- **Fehlerfreundliche Texte:** App-Store-Installation: „Huch, das hat nicht geklappt …“ statt technischer Fehlermeldung.
- **Installer & Docs:** Single-Script-Installer (`create_installer.sh`), systemd-Service (`pi-installer.service`), One-Click-Dokumentation (get.pi-installer.io); Python 3.9+ in Doku und requirements.

---

## [1.2.0.6] – 2026-02

### NAS: Duplikat-Finder (Phase 1)

- **Duplikate & Aufräumen:** Neuer Bereich in der NAS-Seite – fdupes/jdupes installieren, Verzeichnis scannen, Duplikate in Backup verschieben (statt löschen).
- **Installation:** Fallback auf jdupes, wenn fdupes nicht verfügbar; klarere Fehlermeldungen von apt.
- **Scan:** Vorgeschlagener Pfad (Heimatverzeichnis, wenn /mnt/nas nicht existiert); Option „System-/Cache-Verzeichnisse ausschließen“ (.cache, mesa_shader, __pycache__, node_modules, .git, Trash) – Standard: an.
- **API:** `POST /api/nas/duplicates/install`, `POST /api/nas/duplicates/scan`, `POST /api/nas/duplicates/move-to-backup`.
- **Dokumentation:** INSTALL.md – Troubleshooting Duplikat-Finder-Installation; NAS-Dokumentation um Duplikate-Bereich ergänzt.

---

## [1.2.0.5] – 2026-02

### Dokumentation

- **Raspberry Pi 5: Kein Ton über HDMI** – Troubleshooting erweitert: typische Symptome (amixer „cannot find card 0“, /dev/snd/ nur seq/timer, PipeWire nur Dummy Output), Ursache (fehlender Overlay vc4-kms-v3d-pi5), konkrete Schritte. In App-Dokumentation (Troubleshooting), INSTALL.md und PI_OPTIMIZATION.md ergänzt.

---

## [1.2.0.4] – 2026-02

### Pi-Optimierung & Erkennung

- **Pi-Erkennung:** Fallback über Device-Tree (`/proc/device-tree/model`) – Raspberry Pi wird auch erkannt, wenn vcgencmd/cpuinfo fehlschlagen.
- **Raspberry Pi Config:** Menüpunkt erscheint nun zuverlässig, sobald ein Pi erkannt wird.
- **CPU-Auslastung reduziert:** Light-Modus für Polling (`/api/system-info?light=1`); Dashboard-Polling auf dem Pi alle 30 s; Monitoring ohne Live-Polling auf dem Pi; Auslastung nur noch im Dashboard, nicht in Submenüs.
- **UI:** Card-Hover ohne Bewegung (nur Farbwechsel); StatCard-Icon ohne Animation; Hardware & Sensoren: Stats-Merge behält Sensoren/Laufwerke beim Polling.

### Dokumentation

- `PI_OPTIMIZATION.md`: Hinweise zu Pi-Erkennung, Raspberry Pi Config und abschaltbaren Services.

---

## [1.2.0.3] – 2026-02

### Mixer-Installation

- **Backend:** Update und Install in zwei Schritten (`apt-get update`, dann `apt-get install`); Dpkg-Optionen `--force-confdef`/`--force-confold` für nicht-interaktive Installation; bei Fehler wird `copyable_command` zurückgegeben; Timeout-Meldung klarer.
- **Frontend (Musikbox & Kino/Streaming):** Bei Fehler erscheint unter den Mixer-Buttons ein Hinweis „Installation fehlgeschlagen. Manuell im Terminal ausführen:“ mit Befehl und **Kopieren**-Button.

---

## [1.2.0.2] – 2026-02

### Geändert

- **Dashboard – Hardware & Sensoren:** Bereich „Systeminformationen“ entfernt (ist bereits in der Übersicht sichtbar).
- **CPU & Grafik:** Treiber-Hinweise (NVIDIA/AMD/Intel) werden nicht mehr unter der CPU angezeigt, sondern unter der jeweiligen Grafikkarte (iGPU bzw. diskret).

### Dokumentation

- In der Anzeige (Dokumentation → Versionen & Changelog) nur die Endversion mit Details; ältere Updates kompakt bzw. überspringbar.

---

## [1.2.0.1] – 2026-02

### Behoben

- **Dashboard – IP-Adressen:** Text unter den IPs („Mit dieser IP von anderen Geräten erreichbar…“) war anthrazit und bei Hover unleserlich → jetzt `text-slate-200` und Link `text-sky-200`.
- **Dashboard – Updates:** Zeile „X Notwendig · Y Optional“ war zu blass → jetzt `text-slate-200` / `text-slate-100` für bessere Lesbarkeit.
- **Dashboard – Menü:** Buttons „Übersicht“, „Auslastung & Grafik“, „Hardware & Sensoren“ – inaktive Buttons hatten fast gleiche Farbe wie Schrift → jetzt `text-slate-200`, `bg-slate-700/70`, Hover `bg-slate-600`.
- **CPU & Grafik:** Es wurden 32 „Prozessoren“ (Threads) gelistet → ersetzt durch **eine** CPU-Zusammenfassung: Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (aufklappbar), Chipsatz/Mainboard; integrierte Grafik und Grafikkarte unverändert; Auslastung nur noch physikalische Kerne (keine Thread-Liste).
- **Mixer-Installation:** Installation schlug weiterhin fehl → Sudo-Passwort wird getrimmt; `apt-get update -qq` vor install; `DEBIAN_FRONTEND=noninteractive` für update und install; Timeout 180s; Fehlermeldung bis 600 Zeichen; Logging bei Fehler.

### Backend

- `get_cpu_summary()`: Liest aus /proc/cpuinfo und lscpu Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (flags).
- System-Info liefert `cpu_summary`; `hardware.cpus` wird auf einen Eintrag reduziert (keine Liste aller Threads).

---

## [1.2.0.0] – 2026-02

### Neu

- **Musikbox fertig:** Musikbox-Bereich abgeschlossen – Mixer-Buttons (pavucontrol/qpwgraph), Installation der Mixer-Programme per Knopfdruck (pavucontrol & qpwgraph), Sudo-Modal für Mixer-Installation.
- **Mixer:** Mixer in Musikbox und Kino/Streaming eingebaut – „Mixer öffnen (pavucontrol)“ / „Mixer öffnen (qpwgraph)“ starten die GUI-Mixer; „Mixer-Programme installieren“ installiert pavucontrol und qpwgraph per apt; Backend setzt `DISPLAY=:0` für GUI-Start; Installation mit `DEBIAN_FRONTEND=noninteractive` für robuste apt-Installation.
- **Dashboard:** Erweiterungen und Quick-Links; Versionsnummer und Changelog auf 1.2.0.0 aktualisiert.

### API

- `POST /api/system/run-mixer` – Grafischen Mixer starten (Body: `{"app": "pavucontrol"}` oder `{"app": "qpwgraph"}`).
- `POST /api/system/install-mixer-packages` – pavucontrol und qpwgraph installieren (Body optional: `{"sudo_password": "..."}`).

### Dokumentation

- Changelog 1.2.0.0 in App (Dokumentation → Versionen & Changelog).
- Troubleshooting: Mixer-Installation fehlgeschlagen (manueller Befehl, Sudo, DISPLAY) in Dokumentation und INSTALL.md.
- INSTALL.md: API Mixer (run-mixer, install-mixer-packages); FEATURES.md: v1.2 Features; README Version 1.2.0.0.

---

## [1.0.4.0] – 2026-01

- Sicherheit-Anzeige im Dashboard (2/5 aktiviert bei Firewall + Fail2Ban).
- Dokumentation & Changelog aktualisiert.

---

Ältere Einträge siehe **Dokumentation** in der App (Versionen & Changelog).
