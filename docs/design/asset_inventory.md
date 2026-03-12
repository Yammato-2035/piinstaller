## Asset Inventory – Icons & Grafiken (Stand: März 2026)

Ziel: Übersicht über vorhandene UI‑Assets (Icons/Grafiken), ihren Speicherort und den aktuellen Nutzungsstatus.  
Fokus: Dokumentation und Struktur – **keine** neuen Assets oder UI‑Funktionen.

---

### 1. Technische Basis

- **React‑Layer**:
  - `AppIcon` in `frontend/src/components/AppIcon.tsx`
    - Läd SVG‑Dateien aus `/assets/icons/...` (Kategorie‑abhängige Unterordner).
    - Kategorien: `navigation`, `status`, `devices`, `process`, `diagnostic`.
  - Zusätzlich werden an vielen Stellen **Lucide‑Icons** via `lucide-react` genutzt (z. B. `Wifi`, `Database`, `HardDrive`).

- **Aktuelle Icon‑Assets (Build)**:
  - `frontend/dist/assets/icons/...` (38 SVG‑Dateien, generiert)
  - Struktur laut `docs/design/icon_list.md` und `graphics_system.md`:
    - `navigation/`, `status/`, `devices/`, `process/`, `diagnostic/`

- **Design‑Dokumente**:
  - `docs/design/icon_usage.md` – Zuordnung Icons ↔ UI‑Bereiche.
  - `docs/design/icon_list.md` – Vollständige Liste generierter Icons.
  - `docs/design/graphics_system.md` – Grafiksystem (Stil, Kategorien, geplante Illustrationen/Empty States).

---

### 2. Kategorien & vorhandene Dateien

#### 2.1 Navigation

- **Verzeichnis**: `frontend/dist/assets/icons/navigation/`
- **Dateien (Auszug, Stand Repo)**:
  - `icon_dashboard.svg`
  - `icon_installation.svg`
  - `icon_network.svg`
  - `icon_storage.svg`
  - `icon_modules.svg`
  - `icon_settings.svg`
  - `icon_advanced.svg`
  - `icon_diagnose.svg`
  - `icon_help.svg`
- **Verwendung (laut Code + icon_usage)**:
  - Sidebar‑Navigation (`Sidebar.tsx`) über `AppIcon` (`name="dashboard" | "wizard" | "app-store" | "backup" | "settings" | "control-center" | "monitoring" | "periphery-scan" | "documentation"`).
  - Seiten‑Header (z. B. `Dashboard`, `InstallationWizard`, `SettingsPage`, `PeripheryScan`).

#### 2.2 Status

- **Verzeichnis**: `frontend/dist/assets/icons/status/`
- **Dateien (Auszug)**:
  - `status_ok.svg`, `status_warning.svg`, `status_error.svg`
  - `status_active.svg`, `status_running.svg`, `status_loading.svg`
  - `status_complete.svg`, `status_update.svg`
- **Verwendung**:
  - `Dashboard` – Status‑Badges („Alles OK“, „Aktion benötigt“, Fehler).
  - `InstallationWizard` – „Installation läuft“, Abschluss.
  - `StatusItem`‑Bausteine (z. B. Sicherheit/DevEnv/Webserver/Musikbox).
  - Statusfarben via CSS‑Filter (siehe `STATUS_FILTERS` in `AppIcon.tsx`).

#### 2.3 Devices

- **Verzeichnis**: `frontend/dist/assets/icons/devices/`
- **Dateien**:
  - `device_raspberrypi.svg`, `device_sdcard.svg`, `device_nvme.svg`, `device_usb.svg`
  - `device_network.svg`, `device_wifi.svg`, `device_ethernet.svg`
  - `device_display.svg`, `device_audio.svg`
- **Verwendung**:
  - `RaspberryPiConfig` (Header, Karten).
  - `ControlCenter` (WLAN/Display/Audio‑Bereiche – teils als AppIcon, teils zusätzlich Lucide).
  - `BackupRestore` – USB / Datenträger.

#### 2.4 Process

- **Verzeichnis**: `frontend/dist/assets/icons/process/`
- **Dateien**:
  - `process_search.svg`, `process_connect.svg`, `process_prepare.svg`
  - `process_write.svg`, `process_verify.svg`, `process_restart.svg`, `process_complete.svg`
- **Verwendung**:
  - `InstallationWizard` – Schritt‑Icons (Willkommen, Vorbereitung, Zusammenfassung).
  - `PeripheryScan` – Scan‑Aktion.

#### 2.5 Diagnostic

- **Verzeichnis**: `frontend/dist/assets/icons/diagnostic/`
- **Dateien**:
  - `diagnose_error.svg`, `diagnose_logs.svg`, `diagnose_systemcheck.svg`, `diagnose_debug.svg`, `diagnose_test.svg`
- **Verwendung**:
  - Einstellungen/Diagnose‑Tabs (Logs, Systemcheck, Debug).
  - Geplante Bereiche in Control Center / Diagnose (siehe `graphics_system.md`).

---

### 3. Geplante, aber (teilweise) nicht integrierte Assets

Laut `graphics_system.md` gibt es zusätzlich konzipierte Assets:

- **Illustrationen / Empty States** (noch nicht als Dateien im Repo sichtbar):
  - `illus_empty_no_device`, `illus_empty_no_modules`, `illus_empty_no_errors`, `illus_empty_no_network`.
- **Weitere Icons (Design‑Namen)**:
  - `icon_nav_network`, `icon_nav_settings`, `icon_nav_storage` (teilweise abgebildet durch bestehende Dateien, aber andere Namen).
  - `status_ready`, `status_connected`, `status_disconnected` (nicht 1:1 als Dateien vorhanden, ggf. durch vorhandene Status‑Icons abgedeckt).

> **Bewertung**: Diese Assets sind im Design konzipiert, aber im Build‑Output nur teilweise oder gar nicht umgesetzt. Für diese Phase genügt die Dokumentation; keine neuen Dateien anlegen.

---

### 4. Doppeltes System: AppIcon vs. Lucide‑Icons

- **AppIcon (SVG‑based)**:
  - Konsistenter Stil laut Grafiksystem (Outline‑SVG, Farbsteuerung über CSS/Filter).
  - Eingesetzt für Navigation, Status, Geräte, Prozesse, Diagnose.

- **Lucide‑Icons (`lucide-react`)** – Beispiele:
  - `Dashboard.tsx`: `Cpu`, `HardDrive`, `Zap`, `Clock`, `Globe`, `Thermometer`, `Monitor`, `Settings`, `Activity`, etc.
  - `BackupRestore.tsx`: `Database`, `Download`, `Upload`, `Trash2`, `Clock`, `HardDrive`, `Cloud`, `Lock`.
  - `ControlCenter.tsx`: `Wifi` und weitere System‑Icons.

- **Ist‑Zustand**:
  - In vielen Screens werden **beide Systeme parallel** verwendet:
    - Navigation/Status oft über `AppIcon`.
    - Inline‑Piktogramme in Karten, Buttons, Listen via Lucide.
  - Dies ist funktional unkritisch, aber visuell uneinheitlich.

> **Phase‑2‑Bewertung**:  
> - Kein unmittelbarer Laufzeitfehler.  
> - Konsistenzproblem wird nur **dokumentiert**, nicht behoben.  
> - Eine spätere Vereinheitlichung (AppIcon vs. Lucide) ist ein separater Task.

---

### 5. Vorbereitung für spätere Website‑Nutzung

- **Ziel**:
  - Icons und Grafiken sollen sowohl im App‑Frontend als auch in einer späteren Website wiederverwendbar sein.

- **Derzeitiger Stand**:
  - Icons liegen (nach Build) unter `frontend/dist/assets/icons/...` und sind damit primär App‑Output, nicht Quelle.
  - Design‑Docs gehen von einer Quellstruktur `frontend/public/assets/icons/` und `frontend/public/assets/illustrations/` aus.

- **Empfohlene Struktur (nur dokumentiert, noch nicht voll umgesetzt)**:
  - Quell‑Assets:
    - `frontend/public/assets/icons/{navigation,status,devices,process,diagnostic}/...`
    - `frontend/public/assets/illustrations/{install,connect,diagnose,empty_states}/...`
  - Website kann später dieselben Pfade nutzen, unabhängig vom React‑Code.

> In dieser Phase wird **nur** die Struktur beschrieben. Es werden **keine** neuen Ordner oder Dateien angelegt.

---

### 6. Offene B‑Fragen / Inkonsistenzen

1. **AppIcon vs. Lucide‑Icons**  
   - Offen: Welche Bereiche sollen langfristig AppIcon‑basiert sein, welche dürfen Lucide bleiben?
   - Risiko: Uneinheitliche Optik, aber kein Funktionsfehler.

2. **Quelle der Icon‑Assets**  
   - Design‑Docs sprechen von `frontend/public/assets/…`, aktuell sichtbare Dateien liegen unter `frontend/dist/assets/icons/…`.
   - Offen: Wo liegen die „authoritativen“ SVGs (für spätere Website/CI‑Systeme)?

3. **Leere Zustände (Illustrationen)**  
   - Konzept vorhanden, Dateien im Repo nicht sichtbar.
   - Offen: Wann und wo sollen diese Illustrationen eingebunden werden (App vs. Website)?

---

### 7. Selbstprüfung Phase 2 (Assets)

- **Wurde etwas funktional erweitert?**  
  - Nein. Es wurden ausschließlich Bestandsdaten dokumentiert; keine Komponenten oder Routen geändert.

- **Wurde primär dokumentiert?**  
  - Ja. `asset_inventory.md` fasst nur bestehende Dateien/Strukturen zusammen und benennt offene Fragen.

- **Wurden Icons/Grafiken nur strukturell vorbereitet?**  
  - Ja. Es wurde lediglich eine Zielstruktur für spätere Wiederverwendung beschrieben, ohne sie technisch umzusetzen.

- **Ist spätere Website‑Nutzung berücksichtigt, ohne Website zu bauen?**  
  - Ja. Die empfohlene Struktur ist explizit auf spätere Wiederverwendung ausgelegt, bleibt aber auf Dokumentationsebene.

