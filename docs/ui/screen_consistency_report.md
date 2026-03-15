## Screen Consistency Report

_Stand: März 2026 – Abgleich „geplante“ vs. tatsächlich vorhandene Screens._

---

### 1. Übersicht der abgefragten Screens

Zu prüfen waren (Bezeichnungen sinngemäß aus Aufgabenstellung übernommen):

- Welcome
- System Check
- Setup Wizard
- Backup Setup
- Discover Projects
- Apps
- System Status
- Help
- Advanced Features
- Docker Assistant
- DEV Assistant
- Mailserver Assistant

Die folgenden Einschätzungen beziehen sich auf:

- React-Seiten unter `frontend/src/pages/…`
- zentrale Komponenten (`FirstRunWizard`, `Dashboard`, `AppStore`, `BackupRestore`, `InstallationWizard`)
- bestehende Doku (v. a. `docs/Documentation.tsx`-Inhalte und UX-/Architektur-Dokumente)

---

### 2. Screen-Bewertung (existiert? dokumentiert?)

#### 2.1 Welcome

- **Entsprechung im Code**:
  - `frontend/src/components/FirstRunWizard.tsx` – Einstiegsbildschirm mit Begrüßung („Systemcheck“ / Willkommensheadline aus `PlatformContext`).
  - `frontend/src/pages/InstallationWizard.tsx` – Schritt 1 „Willkommen“ im Installationsassistenten.
- **Status**:
  - **Screen existiert** (als Overlays/Seiten in App).
  - In Doku mehrfach erwähnt (First-Run-Wizard, Installationsassistent), aber nicht als eigener „Welcome“-Screen zusammengefasst.

#### 2.2 System Check

- **Entsprechung im Code**:
  - `FirstRunWizard` – erster Schritt „Systemcheck“ (Hardware/Netzstatus).
  - `Dashboard` – System Health / Ressourcenanzeige.
- **Status**:
  - **Funktional vorhanden**, aber über mehrere Screens verteilt (Wizard + Dashboard).
  - In Doku beschrieben (Systemübersicht, Health), jedoch nicht als isolierter „System Check“-Screen dokumentiert.

#### 2.3 Setup Wizard

- **Entsprechung im Code**:
  - `frontend/src/pages/InstallationWizard.tsx` – „Installationsassistent“ mit mehreren Schritten.
  - `Dashboard` / Sidebar bieten Einstieg „Installationsassistent“.
- **Status**:
  - **Screen/Flow existiert** und ist sowohl im Code als auch in Doku (Dokumentation.tsx, Architektur/UX-Pläne) dokumentiert.

#### 2.4 Backup Setup

- **Entsprechung im Code**:
  - `frontend/src/pages/BackupRestore.tsx` – Tab „Backup erstellen“ mit Ziel- und Typwahl (Setup) sowie Backup-Liste/Restore.
- **Status**:
  - **Screen existiert** (Backup & Restore mit Setup-Teil).
  - In Doku (u. a. `Documentation.tsx`) als „Backup & Restore“ beschrieben.

#### 2.5 Discover Projects

- **Entsprechung im Code**:
  - Kein eigenständiger „Discover“-Screen; am ehesten:
    - `AppStore` – Apps auflisten.
    - `FirstRunWizard` – empfohlene Projekte/Apps.
- **Status**:
  - **Kein dedizierter Discover-Screen** im Sinne einer separaten Route.
  - Funktional teilweise durch AppStore/FirstRunWizard abgedeckt, aber kein klarer „Discover Projects“-Namensraum in Code oder Doku.

#### 2.6 Apps

- **Entsprechung im Code**:
  - `frontend/src/pages/AppStore.tsx` – App-Übersicht, App-Liste, Filter.
  - Sidebar-Eintrag „Apps“ → `app-store`.
- **Status**:
  - **App-Store-Screen existiert** und ist in Doku beschrieben („Apps mit einem Klick installieren“).

#### 2.7 System Status

- **Entsprechung im Code**:
  - `Dashboard` – System Health, Ressourcen, Services, Updates.
  - Sidebar „Systemstatus“ (Monitoring).
  - `MonitoringDashboard` – dedizierte Monitoring-Seite.
- **Status**:
  - **Systemstatus-Funktion** ist vorhanden (Dashboard/Monitoring), aber auf mehrere Seiten verteilt.
  - Dokumentation (Dokumentation.tsx, System-Audit) beschreibt diese Bereiche, ohne einen singulären „System Status“-Screen zu definieren.

#### 2.8 Help

- **Entsprechung im Code**:
  - `frontend/src/pages/Documentation.tsx` – In-App-Dokumentation.
  - `HelpTooltip`-Komponente für kontextsensitive Hilfe.
  - Sidebar-Punkt „Hilfe“ → `documentation`.
- **Status**:
  - **Help/Documentation-Screen existiert**, sowohl im Code als auch im Docs-Verzeichnis (`docs/user/*`, `Documentation.tsx`).

#### 2.9 Advanced Features

- **Entsprechung im Code**:
  - Dashboard-Kachel „Erweiterte Funktionen“ → `control-center`.
  - Sidebar-UIMode (Grundlagen/Erweitert/Diagnose) + zusätzliche Seiten (DevEnv, Webserver, Mailserver, NAS, etc.).
- **Status**:
  - **Experten-/Erweiterungsbereiche** sind vorhanden (Control Center, Expertenmodule).
  - Kein einzelner „Advanced Features“-Screen; stattdessen eine Gruppe von Experten-Seiten.

#### 2.10 Docker Assistant

- **Entsprechung im Code**:
  - Keine dedizierte „Docker Assistant“-Seite vorhanden.
  - Docker wird eher als Teil der DevEnv/Server-Setup-Doku adressiert (z. B. in Doku-Texten).
- **Status**:
  - **Screen existiert nicht** als konkrete Seite/Route.

#### 2.11 DEV Assistant

- **Entsprechung im Code**:
  - `frontend/src/pages/DevelopmentEnv.tsx` – Seite für Entwicklungsumgebung.
  - In Doku als „Dev-Umgebung“ beschrieben, nicht explizit als „Assistant“.
- **Status**:
  - **DevEnv-Screen existiert** (Funktionsbereich).
  - Bezeichnung „Assistant“ im Code/Doku nicht etabliert.

#### 2.12 Mailserver Assistant

- **Entsprechung im Code**:
  - `frontend/src/pages/MailServerSetup.tsx` – Mailserver-Konfigurationsseite.
  - UI-Bezeichnung eher „Mailserver“ / „Mailserver einrichten“.
- **Status**:
  - **Mailserver-Konfiguration** ist als Seite vorhanden.
  - Auch hier kein konsistenter „Assistant“-Begriff.

---

### 3. Zusammenfassung Screen-Konsistenz

- **Existierende Screens/Flows**:
  - Welcome/Systemcheck (FirstRunWizard/InstallationWizard).
  - Setup Wizard (InstallationWizard).
  - Backup Setup (BackupRestore).
  - Apps (AppStore).
  - System Status (Dashboard + Monitoring).
  - Help (Documentation).
  - Advanced Features (ControlCenter + Expertenmodule).
  - DEV-/Mailserver-Bereiche (DevelopmentEnv, MailServerSetup).

- **Fehlende / nur konzeptionelle Screens**:
  - Discover Projects – kein dedizierter Screen, nur verteilt über Wizard/AppStore.
  - Docker Assistant – aktuell kein eigener Screen.
  - „Assistant“-Begriffe (Dev/Mail) – im Code primär als *Setup*- oder *Env*-Seiten realisiert, nicht als explizite Assistenten.

---

### 4. Empfehlungen (nur Dokumentation)

1. **Namensmapping dokumentieren**  
   - In einem separaten Dokument (oder Anhang in der Architektur-Doku) klarstellen, welche internen Seitennamen (`Dashboard`, `InstallationWizard`, `BackupRestore`, `AppStore`, `DevelopmentEnv`, `MailServerSetup`, `ControlCenter`) welchen fachlichen „Screens“ (z. B. „System Status“, „Apps“, „Mailserver Assistant“) entsprechen.

2. **Konzeptionelle Screens kennzeichnen**  
   - In bestehenden Planungs- oder UX-Dokumenten kenntlich machen, welche Screens aktuell **nur** konzeptionell vorhanden sind (z. B. „Discover Projects“, „Docker Assistant“), um falsche Erwartungen zu vermeiden.

3. **Keine Assistenten nachrüsten**  
   - Entsprechend der Leitlinie dieser Phase: keine neuen „Assistant“-Flows im Code anlegen, lediglich in der Doku klären, welche bestehenden Seiten diese Rollen teilweise abdecken.

---

### 5. Selbstprüfung Phase 7

- **Keine neuen Screens / Assistenten erstellt?**  
  - Ja. Es wurden nur existierende Seiten beschrieben und gegen die gewünschte Screen-Liste abgeglichen.

- **Nur Dokumentation und Konsistenzprüfung?**  
  - Ja. Code, Routen und Komponenten blieben unverändert.

- **Folgefehler betrachtet?**  
  - Ja. Insbesondere die Gefahr, dass konzeptionell geplante Screens („Discover Projects“, „Docker Assistant“) irrtümlich als „schon vorhanden“ angenommen werden, ist explizit dokumentiert.

