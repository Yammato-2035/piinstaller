## Frontend-Struktur – Schnellüberblick

_Zweck: Orientierung für Entwickler im React-/Tauri-Frontend._

---

### 1. Verzeichnisbaum (vereinfacht)

```text
frontend/
  src/
    App.tsx                 # Hauptrahmen, Sidebar, Routing-Logik
    main.tsx                # Einstiegspunkt (ReactDOM)
    pages/                  # Seiten (Dashboard, BackupRestore, Settings, ...)
    components/             # Wiederverwendbare UI-Bausteine (AppIcon, Dialoge, ...)
    context/                # React-Contexts (PlatformContext, UIModeContext, ...)
    config/                 # z. B. riskLevels.ts
    features/remote/        # Linux Companion / Remote-View
  public/
    assets/icons/**         # SVG-Icons (Navigation, Status, Devices, Process, Diagnostic)
  src-tauri/                # Tauri-Config für Desktop-App (optional)
  package.json              # Dependencies, Scripts
  vite.config.ts            # Vite-Konfiguration
```

---

### 2. Kernkomponenten

- **`App.tsx`**
  - Verwaltet:
    - aktuelle Seite (`currentPage`)
    - Theme (hell/dunkel/system)
    - FirstRunWizard-Overlay
    - Sidebar + Mobile-Menü
  - Bindet u. a. ein:
    - `Sidebar`
    - `SudoPasswordDialog`
    - `RunningBackupModal`
    - `Dashboard`, `BackupRestore`, `InstallationWizard`, `SettingsPage`, `ControlCenter`, `AppStore`, ...

- **`Sidebar.tsx`**
  - Navigation zwischen Seiten.
  - UIMode (Grundlagen/Erweitert/Diagnose).
  - Anzeige von App-Titel und Version.

- **Seiten unter `pages/` (Auszug)**:
  - `Dashboard.tsx` – Systemübersicht, Health, Module.
  - `BackupRestore.tsx` – Backups erstellen/auflisten/wiederherstellen.
  - `InstallationWizard.tsx` – Installationsassistent (mehrstufig).
  - `SettingsPage.tsx` – Einstellungen (allgemein, Server-URL, Logs, etc.).
  - `SecuritySetup.tsx`, `WebServerSetup.tsx`, `MailServerSetup.tsx`, `NASSetup.tsx`, `HomeAutomationSetup.tsx`, `MusicBoxSetup.tsx`, `DevelopmentEnv.tsx` – Modul-/Setup-Seiten.
  - `RaspberryPiConfig.tsx`, `ControlCenter.tsx`, `PeripheryScan.tsx` – System-/Hardware-nahe Bereiche.
  - `Documentation.tsx` – In-App-Dokumentation.
  - `AppStore.tsx` – Apps/Projekte.

---

### 3. Zustands- und Kontext-Ebenen

- **PlatformContext (`context/PlatformContext.tsx`)**
  - Stellt Infos wie `systemLabel`, `appTitle`, `wizardWelcomeHeadline` bereit.

- **UIModeContext (`context/UIModeContext.tsx`)**
  - Steuert, ob die UI im Modus Grundlagen / Erweitert / Diagnose arbeitet.
  - Beeinflusst u. a. sichtbare Einträge in der Sidebar und Beginner-Startansicht.

- **Lokaler Component-State**
  - Pro Seite für Eingaben, Ladezustände, etc. (z. B. `BackupRestore`: Backup-Tabs, Ziele, laufender Job).

---

### 4. API-Anbindung

- **`frontend/src/api.ts`**
  - Wrapper um `fetch` mit Basis-URL (Backend).
  - Wird in Seiten/Komponenten verwendet, um `/api/...`-Endpunkte aufzurufen.

---

### 5. Assets (Frontend-seitig)

- Icons: über `AppIcon` (`components/AppIcon.tsx`) aus `/assets/icons/**`.
- Konkrete Asset-/Icon-Details siehe:
  - `docs/design/asset_inventory_complete.md`
  - `docs/design/asset_inventory.md`
  - `docs/design/icon_list.md`
  - `docs/design/graphics_system.md`

---

### 6. Selbstprüfung (Phase 9 – Frontend-Struktur)

- **Architektur/Funktion erweitert?** – Nein, nur vorhandene Struktur beschrieben.

