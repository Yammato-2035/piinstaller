## Vollständiges Grafik- und Icon-Inventar

_Stand: März 2026 – Konsolidierte Sicht auf alle bekannten Icons, Grafiken und geplanten Assets._

---

### 1. Quellen im Repository

- **Frontend-Quell-Assets**  
  - `frontend/public/assets/icons/**` – SVG-Icons, gruppiert nach:
    - `navigation/`
    - `status/`
    - `devices/`
    - `process/`
    - `diagnostic/`

- **Frontend-Build-Assets**  
  - `frontend/dist/assets/icons/**` – gleiche Struktur, generierte/veröffentlichte Version der Icons.
  - `frontend/dist/docs/screenshots/README.md` – Hinweis auf Screenshots, aber keine PNGs/JPGs im Repo sichtbar.

- **Design- und Dokumentationsquellen**  
  - `docs/design/icon_list.md` – Auflistung aller generierten Icons (Name, Kategorie, Beschreibung).
  - `docs/design/icon_usage.md` – Mapping Icons ↔ UI-Bereiche.
  - `docs/design/graphics_system.md` – übergreifendes Grafiksystem (Icons + Illustrationen + leere Zustände).
  - `docs/design/asset_inventory.md` – bereits vorhandenes, fokussiertes Inventar (AppIcon + Lucide-Icons).

---

### 2. Icon-Kategorien (Stand Quell-Assets)

#### 2.1 Navigation

- **Pfad**: `frontend/public/assets/icons/navigation/`
- **Icons (Auszug, laut Repo)**:
  - `icon_dashboard.svg`
  - `icon_installation.svg`
  - `icon_network.svg`
  - `icon_storage.svg`
  - `icon_modules.svg`
  - `icon_settings.svg`
  - `icon_advanced.svg`
  - `icon_diagnose.svg`
  - `icon_help.svg`

**Verwendung**:

- Sidebar (Start, Setup-Assistent, Apps, Backup, Systemstatus, Hilfe, Erweiterte Funktionen).
- Seiten-Header (z. B. Dashboard, Installationsassistent, Einstellungen, Peripherie-Scan).

#### 2.2 Status

- **Pfad**: `frontend/public/assets/icons/status/`
- **Icons**:
  - `status_ok.svg`, `status_warning.svg`, `status_error.svg`
  - `status_active.svg`, `status_running.svg`, `status_loading.svg`
  - `status_complete.svg`, `status_update.svg`

**Verwendung**:

- Dashboard-Hero („Alles OK“, „Aktion benötigt“, Fehler).
- InstallationWizard („Installation läuft“, Abschluss).
- Status-Badges (Sicherheit, DevEnv, Webserver, Musikbox etc.).

#### 2.3 Devices

- **Pfad**: `frontend/public/assets/icons/devices/`
- **Icons**:
  - `device_raspberrypi.svg`, `device_sdcard.svg`, `device_nvme.svg`, `device_usb.svg`
  - `device_network.svg`, `device_wifi.svg`, `device_ethernet.svg`
  - `device_display.svg`, `device_audio.svg`

**Verwendung**:

- RaspberryPiConfig (Header und Karten).
- ControlCenter (WLAN, Display, Audio – teils gemischt mit Lucide).
- BackupRestore (USB / Datenträger).

#### 2.4 Process

- **Pfad**: `frontend/public/assets/icons/process/`
- **Icons**:
  - `process_search.svg`, `process_connect.svg`, `process_prepare.svg`
  - `process_write.svg`, `process_verify.svg`, `process_restart.svg`, `process_complete.svg`

**Verwendung**:

- Installationsassistent (Schritt-Icons: Willkommen, Vorbereitung, Zusammenfassung).
- PeripheryScan (Scan-Aktionen).

#### 2.5 Diagnostic

- **Pfad**: `frontend/public/assets/icons/diagnostic/`
- **Icons**:
  - `diagnose_error.svg`, `diagnose_logs.svg`, `diagnose_systemcheck.svg`, `diagnose_debug.svg`, `diagnose_test.svg`

**Verwendung**:

- Diagnose-/Logbereiche (Einstellungen, Dashboard, evtl. künftige Diagnose-Screens).

---

### 3. Gemischte Icon-Systeme

- **AppIcon-basierte Icons**  
  - Definiert in `frontend/src/components/AppIcon.tsx`.  
  - Nutzt die oben genannten Kategorien und Dateinamen.  
  - Starke Nutzung in:
    - Sidebar, Seiten-Header
    - Status-Badges im Dashboard
    - Geräte-/Prozess-Icons in BackupRestore, RaspberryPiConfig, ControlCenter

- **Lucide-Icons (`lucide-react`)**  
  - Direkt importierte React-Icons (z. B. `Cpu`, `HardDrive`, `Wifi`, `Database`, `Zap`, `Globe`, `Settings`, `Copy`, `Trash2` usw.).
  - Eingesetzt für:
    - Inline-Icons in Karten/Buttons.
    - Detailbereiche in Dashboard, BackupRestore, ControlCenter, SettingsPage, AppStore etc.

**Ist-Zustand:**  
Beide Systeme werden parallel eingesetzt; stilistisch nicht vollständig vereinheitlicht, funktional aber stabil. Diese Parallelität ist als bewusstes Konsistenzthema dokumentiert (siehe `asset_inventory.md` und `priority_b_fixes.md`), nicht als Fehler.

---

### 4. Fehlende Illustrationen und Website-bezogene Assets

Aus `docs/design/graphics_system.md`:

- **Konzept-Illustrationen (Empty States):**
  - `illus_empty_no_device`
  - `illus_empty_no_modules`
  - `illus_empty_no_errors`
  - `illus_empty_no_network`

**Ist-Stand im Repo:**

- Keine entsprechenden Dateien in `frontend/public/assets/illustrations/**` oder `frontend/dist/assets/**` sichtbar.
- Screenshots werden in der Doku referenziert (z. B. `docs/screenshots/screenshot-*.png`, `/docs/screenshots/screenshot-backup.png`), aber ein vollständiger Screenshot-Ordner ist im Repository nicht enthalten – nur ein README unter `frontend/dist/docs/screenshots/`.

---

### 5. Zielstruktur für Assets

Nur strukturell definiert, **keine neuen Dateien angelegt**:

```text
assets/
  icons/
    navigation/      # Menü, Hauptbereiche (Dashboard, Setup, Backup, Hilfe, ... )
    status/          # OK, Warnung, Fehler, Läuft, Aktiv, Abgeschlossen, Update
    devices/         # Raspberry Pi, SD, NVMe, USB, Netzwerk, WLAN, Display, Audio
    process/         # Suchen, Verbinden, Vorbereiten, Schreiben, Prüfen, Neustart
    diagnostic/      # Fehler, Logs, Systemcheck, Debug, Test

  illustrations/
    install/         # Installations-/Wizard-Illustrationen
    connect/         # Remote/Verbindungs-Flows
    diagnose/        # Diagnose-/Fehlersuch-Motive
    empty_states/    # Kein Gerät, keine Module, keine Fehler, kein Netzwerk

  website/
    hero/            # Hero-Grafiken für Landingpage
    sections/        # Bereichsillustrationen (Sicherheit, Backup, Apps, Remote)
    icons/           # ggf. Subset der App-Icons mit Web-spezifischem Zuschnitt
```

**Zielbild:**

- **App**:
  - Nutzt `assets/icons` und `assets/illustrations` (über `public/`-Pfad), vor allem für Navigation, Status, Geräte und leere Zustände.
- **Website**:
  - Nutzt dieselben Icons und Illustrationen, ggf. ergänzt um eigenständige Hero-/Section-Grafiken in `assets/website/`.

---

### 6. Offene Punkte (nur dokumentiert)

1. **Master-Quelle für Icons**  
   - Noch nicht eindeutig festgelegt, ob `frontend/public/assets/icons` oder ein externer Design-Ordner als „Single Source of Truth“ dienen soll.

2. **Fehlende Illustrationen**  
   - Empty-State-Motive existieren nur in der Doku, nicht als Dateien.

3. **Screenshots**  
   - Doku verweist auf mehrere Screenshot-Dateien, die im Repo fehlen; eine zentrale Ablage (z. B. unter `assets/website/` oder `docs/assets/`) ist noch zu definieren.

---

### 7. Selbstprüfung Phase 6

- **Keine neuen Icons generiert?**  
  - Ja. Es wurden nur vorhandene Assets und Strukturen inventarisiert und eine Zielstruktur beschrieben.

- **Nur Struktur definiert und fehlende Assets dokumentiert?**  
  - Ja. Die Zielstruktur unter `assets/` ist rein konzeptionell, ohne Änderungen an Build oder Code.

- **Gemischte Icon-Systeme nur beschrieben, nicht umgebaut?**  
  - Ja. AppIcon/Lucide-Betrieb bleibt unverändert; das Thema ist als Konsistenzpunkt festgehalten.

