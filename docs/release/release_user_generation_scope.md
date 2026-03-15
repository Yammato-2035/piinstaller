# Release-Version: Benutzerfunktionen und Vorlagen/Presets

In der **RELEASE-Version** (APP_EDITION=release) sieht der Endnutzer nur Funktionen, die dazu dienen, aus dem PI die gewünschte **Produktionsmaschine** zu machen. Keine Entwickler- oder Packaging-Funktionen.

---

## In der Release-Version sichtbare Benutzerfunktionen

Nutzer können weiterhin vorhandene Strukturen nutzen:

- **Setup-Assistent (wizard)** – geführte Einrichtung, Zielsysteme und Schritte auswählen
- **Voreinstellungen (presets)** – vorbereitete Konfigurationen und Profile anwenden
- **Apps (app-store)** – Katalog-Apps installieren (z. B. Home Assistant, Nextcloud, Pi-hole, Jellyfin, DSI-Radio-Setup, WordPress, Code-Server, Node-RED)
- **Backup** – Sicherungen anlegen, wiederherstellen, Cloud/USB
- **Systemstatus (monitoring)** – Überwachung und Status
- **Hilfe (documentation)** – Nutzerdokumentation
- **Einstellungen (settings)** – Theme, Erfahrungsstufe, Backend-URL
- **Sicherheit (security)** – Firewall, Scan, Konfiguration
- **Benutzer (users)** – Systembenutzer verwalten
- **Control Center** – WLAN, Display, Bluetooth
- **Peripherie-Scan** – Hardware erkennen
- **Webserver, NAS, Hausautomatisierung, Musikbox, Kino/Streaming, Lerncomputer** – jeweilige Setup- und Konfigurationsseiten
- **Raspberry Pi Config** – (nur auf Pi) Konfiguration des Geräts
- **Linux Companion (remote)** – Remote-Steuerung/Pairing
- **DSI-Radio Einstellungen** – (bei Freenove) Radio-Konfiguration

Vorlagen, Presets und Zielprofile werden über **Setup-Assistent** und **Voreinstellungen** ausgewählt und angewendet; der Fokus liegt auf verständlichen Endnutzertexten und klarer Benutzerführung.

---

## In der Release-Version nicht vorhanden

- **PI-Installer Update (Expertenmodul)** – kein Menüeintrag, keine Route, keine Update-Center-API (DEB-Build, Kompatibilitätsprüfung, Release-Freigabe, Build-Historie). Diese Funktionalität existiert ausschließlich im **REPO-Modus** (APP_EDITION=repo).
- Keine Packaging- oder Entwicklersprache in der für Release bestimmten UI.
- Dev-Umgebung und Mailserver bleiben (bei experienceLevel „developer“) verfügbar; für reine Endnutzer-Release-Fassung können diese bei Bedarf ebenfalls ausgeblendet oder eingeschränkt werden.

---

## Zielsysteme / Profile (bereits im Projekt)

Typische Zielsysteme, die über Wizard/Presets/App-Store abgedeckt werden können:

- NAS, Medienserver, Smart Home (Home Assistant), Lerncomputer, Musik-/Audio-Station, Webserver, Mailserver (developerOnly), Retro-Gaming (falls integriert), DSI-Radio (Freenove).

Die Release-Fassung zeigt nur die Auswahl der gewünschten Zielmaschine und die passenden vorbereiteten Vorlagen/Presets; keine internen Build- oder Release-Funktionen.
