## Website Asset Reuse Plan

_Stand: März 2026 – Vorbereitung der Wiederverwendung bestehender UI-Assets auf einer zukünftigen Website._

---

### 1. Zielsetzung

- Bestehende **Icons**, **Illustrationen** (zukünftig) und ggf. **Screenshots** sollen:
  - sowohl in der App (React/Tauri) als auch
  - in einer späteren Website (Landingpage, Docs, Handbuch)
  eingesetzt werden.
- Vermeidung von Duplikaten:
  - Eine gemeinsame Asset-Basis unter `assets/…` (bzw. `frontend/public/assets/…`).

---

### 2. Wiederverwendbare UI-Elemente aus der App

**Geeignete UI-Muster/Elemente für Website-Reuse (konzeptionell, nicht als Code-Kopie):**

- **Dashboard-Karten**:
  - Systemstatus/Health, Ressourcen-Karten (CPU, RAM, Speicher, Temperatur).
  - Eignung: Darstellung von „Was macht der PI-Installer?“ mit klaren Status-Icons.

- **Aufgaben-Kacheln (Beginner-Startseite)**:
  - „System einrichten“, „Apps installieren“, „Backup erstellen“, „Systemzustand prüfen“, „Lernen & entdecken“, „Erweiterte Funktionen“.
  - Eignung: Landingpage-Sektionen, die die Haupt-Use-Cases erklären.

- **Backup & Restore-Flow (Wizard-ähnliche Darstellung)**:
  - Besonders geeignet für Dokumentationsseiten („So sicherst du dein System“).

- **AppStore-Listen**:
  - Karten für Apps/Projekte (Home Assistant, Nextcloud, Pi-hole, Jellyfin, etc.).
  - Eignung: Projekt-/Feature-Übersichten auf der Website.

- **ControlCenter- und RaspberryPiConfig-Abschnitte**:
  - Strukturiert nach Bereichen (WLAN, Display, Audio, Performance, etc.).
  - Eignung: Dokumentation technischer Features mit dazugehörigen Icons.

> Diese Elemente sollen **inhaltlich und visuell** wiederverwendet werden (Layout-Ideen, Icons, Texte), nicht als 1:1 kopierte React-Komponenten.

---

### 3. Bestehende Assets, die direkt web-tauglich sind

- **Icons aus `assets/icons/`** (siehe `asset_inventory_complete.md`):
  - Navigation: Dashboard, Installation, Storage, Settings, Help, Advanced, Diagnose, Modules.
  - Status: OK, Warnung, Fehler, Läuft, Aktiv, Abgeschlossen, Update.
  - Devices: Raspberry Pi, SD, NVMe, USB, Netzwerk, WLAN, Ethernet, Display, Audio.
  - Process: Search, Connect, Prepare, Write, Verify, Restart, Complete.
  - Diagnostic: Error, Logs, Systemcheck, Debug, Test.

**Web-Einsatzmöglichkeiten:**

- Landingpage:
  - Navigation-Icons für Sektionen (Sicherheit, Backup, Apps, Remote).
- Dokumentationsseiten:
  - Status-/Hinweis-Boxen mit Status-Icons.
  - Geräte-Abschnitte (z. B. Pi-Modelle, Speicheraufbau) mit Device-Icons.

---

### 4. Fehlende Website-spezifische Assets (nur dokumentiert)

Für eine eigenständige Website wären zusätzliche Grafiken sinnvoll, die aktuell noch **nicht** existieren:

1. **Hero-Grafiken**:
   - Beispiel: „PI-Installer auf einem Raspberry Pi“, abstrakte Visualisierung des Dashboards.
   - Kategorie: `assets/website/hero/…`

2. **Section-Illustrationen**:
   - Sicherheit (Firewall/Updates), Backup, Apps/Projekte, Remote/Companion, Ressourcen-Management.
   - Kategorie: `assets/website/sections/…`

3. **Leere Zustände/Web-spezifische Illustrationen**:
   - Übernahme oder Erweiterung der geplanten Empty-States (`empty_states/`).

> In dieser Phase werden diese Assets **nur benannt**, nicht erstellt.

---

### 5. Empfohlene gemeinsame Asset-Struktur (App + Website)

```text
frontend/public/assets/
  icons/               # Alle Icons, App + Website
    navigation/
    status/
    devices/
    process/
    diagnostic/

  illustrations/       # Geteilte Illustrationen
    install/
    connect/
    diagnose/
    empty_states/

  website/             # Website-spezifische Visuals
    hero/
    sections/
    screenshots/       # Kuratierte Screenshots für Website
```

- **App**:
  - Nutzt `icons/` und ggf. `illustrations/empty_states/`.
- **Website**:
  - Nutzt `icons/` für konsistente Symbolsprache.
  - Nutzt `illustrations/` und `website/` für Branding und erklärende Grafiken.

---

### 6. Offene Punkte / Folgeaufgaben

1. **Screenshots-Quelle definieren**
   - Derzeit verweisen verschiedene Doku-Dateien auf `docs/screenshots/…`.
   - Für eine Website wäre ein konsistenter Pfad (`frontend/public/assets/website/screenshots/…`) wünschenswert.

2. **Konkretes Design-Briefing für Website-Grafiken**
   - Basierend auf `graphics_system.md` und den Beginner-First-Konzepten sollten Hero- und Section-Grafiken gezielt beauftragt werden.

3. **Keine Kopplung an App-Build erzwingen**
   - Website sollte statische Assets nutzen können, ohne zwingend den App-Build ausführen zu müssen (Assets als echte Quellen, nicht nur Build-Artefakte).

---

### 7. Selbstprüfung Phase 8

- **Wurden UI-Elemente nur für spätere Wiederverwendung identifiziert, nicht umgesetzt?**  
  - Ja. Es wurden ausschließlich vorhandene Muster und potenzielle Einsatzszenarien beschrieben.

- **Wurden Icons/Illustrationen nicht neu erzeugt?**  
  - Ja. Alle genannten zusätzlichen Assets (Hero, Section-Illustrationen) sind nur als Bedarf dokumentiert.

- **Keine Architektur-/Funktionserweiterung?**  
  - Ja. Weder App- noch Website-Code wurde angefasst; es handelt sich rein um Planungsdokumentation.

