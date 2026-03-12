## UI-Flow – Entwicklerüberblick

_Zweck: Beschreibt, wie Nutzer typischerweise durch die wichtigsten UI-Bereiche geführt werden._

---

### 1. Erster Start / First-Run-Wizard

1. **App-Start**
   - `App.tsx` lädt Systeminformationen und prüft, ob `FIRST_RUN_DONE_KEY` im `localStorage` gesetzt ist.
2. **FirstRunWizard**
   - Komponente `FirstRunWizard` wird als Overlay angezeigt, solange `firstRunDone === false`.
   - Schritte:
     - Systemcheck (Hardware, RAM, Speicher, Netzwerk).
     - Erfahrungslevel (Beginner / Advanced / Developer).
     - Empfohlene erste Schritte (Kacheln: System einrichten, Apps installieren, Backup erstellen etc.).
     - Interessen/empfohlene Apps (optional).
   - Abschluss:
     - Setzt `FIRST_RUN_DONE_KEY`.
     - Navigiert standardmäßig zur Startseite (`dashboard`).

---

### 2. Startseite / Dashboard

- Komponente: `Dashboard.tsx`.
- Funktionen:
  - Beginner-First-Aufgaben-Kacheln (System einrichten, Apps installieren, Backup erstellen, Systemzustand prüfen, Lernen & entdecken, Erweiterte Funktionen).
  - Systemstatus (Health, Ressourcen, Updates).
  - Modulübersicht (Sicherheit, Benutzer, DevEnv, Webserver, Mailserver, NAS, Hausautomation, Musikbox, Presets, Lerncomputer, Monitoring, Backup).
  - Schnellstart-Abschnitt: „Installationsassistent starten“.

Der sichtbare Umfang hängt vom UI-Modus (Grundlagen vs. Erweitert/Diagnose) und vom Experience-Level ab.

---

### 3. Navigationskonzept

- **Sidebar (`Sidebar.tsx`)**
  - Zeigt je nach Experience-Level und UIMode:
    - Basis-Einträge: Start, Setup-Assistent, Apps, Backup, Systemstatus, Hilfe.
    - Erweiterte Module: Remote, Control Center, NAS, Webserver, Mailserver, DevEnv, Monitoring, Periphery-Scan, RaspberryPiConfig etc.
  - UIMode-Tabs: Grundlagen / Erweitert / Diagnose (für Fortgeschrittene sichtbar).

- **Seitenwechsel**
  - `App.tsx` verwaltet `currentPage` und rendert die entsprechende Page-Komponente (`Dashboard`, `BackupRestore`, `InstallationWizard`, `SettingsPage`, `...`).

---

### 4. Wichtige Flows

#### 4.1 System einrichten (Setup Wizard)

1. Einstieg:
   - Über Dashboard-Kachel „System einrichten“ oder Sidebar „Setup-Assistent“.
2. Komponente:
   - `InstallationWizard.tsx` mit mehreren Schritten (Willkommen, Sicherheit, Benutzer, DevEnv, Webserver, Zusammenfassung).
3. Ziel:
   - Systemgrundkonfiguration (Sicherheit, Nutzer, Dev-Umgebung, Webserver) anstoßen.

#### 4.2 Backup & Restore

1. Einstieg:
   - Dashboard-Kachel „Backup erstellen“.
   - Sidebar-Eintrag „Backup“ → `BackupRestore`.
2. Komponente:
   - `BackupRestore.tsx` mit Tabs:
     - „Backup erstellen“
     - „Vorhandene Backups“
     - „Einstellungen“ / „Klonen“ (je nach Implementierung).
3. Ziel:
   - Backups erstellen, anzeigen, verifizieren, wiederherstellen; optional USB/Cloud.

#### 4.3 Apps & Projekte

1. Einstieg:
   - Dashboard-Kachel „Apps installieren“.
   - Sidebar „Apps“ → `AppStore`.
2. Komponente:
   - `AppStore.tsx` – Liste von Apps/Projekten.

---

### 5. Hilfesystem

- **In-App-Dokumentation**
  - `Documentation.tsx` spiegelt relevante Teile der Markdown-Dokumentation wider.

- **Kontextsensitive Hilfe**
  - `HelpTooltip`-Komponente (Fragezeichen-Icon + Tooltip) für technische Optionen.

---

### 6. UI-Modi & Experience-Level

- Experience-Level (Beginner / Advanced / Developer)
  - Gelesen aus `FirstRunWizard` / Profil-API (`/api/user-profile`).

- UIMode (Grundlagen / Erweitert / Diagnose)
  - Steuert, welche Module/Seiten und welche Informationen in der Sidebar/Seiten sichtbar sind.

Weitere Details: `docs/architecture/ui_modes.md`, `docs/architecture/foundation_vs_advanced_map.md`.

---

### 7. Selbstprüfung (Phase 9 – UI-Flow)

- **Neue Flows eingeführt?** – Nein, bestehende Flows wurden nur beschrieben.
- **Assistenten/Seiten neu definiert?** – Nein, es wird explizit auf vorhandene Komponenten verwiesen.

