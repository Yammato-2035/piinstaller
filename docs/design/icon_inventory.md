# Icon-Inventar – PI-Installer

_Stand: März 2026 – Vollständige Übersicht aller Icons unter `frontend/public/assets/icons/`._

---

## 1. Quellverzeichnis

- **Pfad:** `frontend/public/assets/icons/`
- **Unterordner:** `navigation/`, `status/`, `devices/`, `process/`, `diagnostic/`
- **Format:** SVG, einheitlich nutzbar über die Komponente `AppIcon` (`frontend/src/components/AppIcon.tsx`)

---

## 2. Vorhandene Icons nach Kategorie

### 2.1 Navigation (9 Dateien)

| Datei | AppIcon-Name(n) | Verwendung im Code |
|-------|------------------|---------------------|
| `icon_dashboard.svg` | `dashboard` | Dashboard-Seite, Sidebar „Start“ |
| `icon_installation.svg` | `installation`, `wizard` | Setup-Assistent, Installationswizard, FirstRunWizard-Karten |
| `icon_network.svg` | `network` | (in AppIcon gemappt, Nutzung optional) |
| `icon_storage.svg` | `storage`, `backup` | Sidebar „Backup“, Dashboard-Kachel Backup, BackupRestore |
| `icon_modules.svg` | `modules`, `app-store` | Sidebar „Apps“, App Store, Dashboard-Kachel Apps |
| `icon_settings.svg` | `settings` | Sidebar „Einstellungen“, SettingsPage |
| `icon_advanced.svg` | `advanced`, `control-center` | Sidebar „Control Center“, Dashboard „Erweiterte Funktionen“ |
| `icon_diagnose.svg` | `diagnose`, `periphery-scan`, `monitoring` | Sidebar „Systemstatus“, „Peripherie-Scan“, PeripheryScan, Diagnose-Tabs |
| `icon_help.svg` | `help`, `documentation` | Sidebar „Hilfe“, Documentation-Seite |

### 2.2 Status (8 Dateien)

| Datei | AppIcon-Name | statusColor | Verwendung im Code |
|-------|--------------|-------------|---------------------|
| `status_ok.svg` | `ok` | ok (grün) | Dashboard Hero, Sidebar Footer „Bereit“, StatusItem aktiv |
| `status_warning.svg` | `warning` | warning (gelb) | Dashboard Hero „Aktion benötigt“, StatusItem inaktiv |
| `status_error.svg` | `error` | error (rot) | Dashboard Hero Fehler, Backend-Fehlerkarte |
| `status_loading.svg` | `loading` | — | (in AppIcon gemappt) |
| `status_active.svg` | `active` | — | (in AppIcon gemappt) |
| `status_complete.svg` | `complete` | ok/muted | Dashboard „Installation Status“ |
| `status_running.svg` | `running` | ok | InstallationWizard „Installation läuft“ |
| `status_update.svg` | — | — | **Nicht in AppIcon gemappt** – Datei vorhanden, keine Code-Nutzung |

### 2.3 Devices (9 Dateien)

| Datei | AppIcon-Name | Verwendung im Code |
|-------|--------------|---------------------|
| `device_raspberrypi.svg` | `raspberrypi` | RaspberryPiConfig Header |
| `device_sdcard.svg` | `sdcard` | (in AppIcon gemappt) |
| `device_nvme.svg` | `nvme` | (in AppIcon gemappt) |
| `device_usb.svg` | `usb` | BackupRestore „USB / Datenträger“ |
| `device_wifi.svg` | `wifi` | ControlCenter WLAN-Bereich |
| `device_ethernet.svg` | `ethernet` | (in AppIcon gemappt) |
| `device_display.svg` | `display` | ControlCenter Display-Bereich |
| `device_audio.svg` | `audio` | (in AppIcon gemappt) |
| `device_network.svg` | — | **Nicht in AppIcon DEVICE_MAP** – Datei vorhanden, „network“ nutzt navigation/icon_network.svg |

### 2.4 Process (7 Dateien)

| Datei | AppIcon-Name | Verwendung im Code |
|-------|--------------|---------------------|
| `process_search.svg` | `search` | PeripheryScan „Assimilation starten“ |
| `process_connect.svg` | `connect` | InstallationWizard Schritt 1 Willkommen |
| `process_prepare.svg` | `prepare` | InstallationWizard Schritte 2–5 |
| `process_write.svg` | `write` | (in AppIcon gemappt) |
| `process_verify.svg` | `verify` | (in AppIcon gemappt) |
| `process_restart.svg` | `restart` | (in AppIcon gemappt) |
| `process_complete.svg` | `complete` | InstallationWizard Schritt 6 Zusammenfassung |

### 2.5 Diagnostic (5 Dateien)

| Datei | AppIcon-Name | Verwendung im Code |
|-------|--------------|---------------------|
| `diagnose_error.svg` | `error` | (category diagnostic) |
| `diagnose_logs.svg` | `logs` | SettingsPage Logs-Tab |
| `diagnose_systemcheck.svg` | `systemcheck` | (in AppIcon gemappt) |
| `diagnose_debug.svg` | `debug` | (in AppIcon gemappt) |
| `diagnose_test.svg` | `test` | (in AppIcon gemappt) |

---

## 3. Nutzung im Code (Zusammenfassung)

- **AppIcon** wird verwendet in:
  - `Sidebar.tsx` – Navigation, Footer-Status
  - `Dashboard.tsx` – Kacheln, Hero-Status, Modulübersicht, Backend-Fehler
  - `FirstRunWizard.tsx` – Karten (icon aus FIRST_STEPS_CARDS)
  - `InstallationWizard.tsx` – Schritte, Header, „Installation läuft“
  - `BackupRestore.tsx` – USB-Ziel
  - `SettingsPage.tsx` – Header, Logs-Tab
  - `PeripheryScan.tsx` – Header, Scan-Button
  - `RaspberryPiConfig.tsx` – Header
  - `ControlCenter.tsx` – Sektions-Icons (appIcon pro Section)

- **Zusätzlich:** Viele Seiten nutzen parallel **Lucide-Icons** (`lucide-react`) für Inline-Symbole (z. B. Cpu, HardDrive, Database, Wifi). Das ist dokumentiert, kein Datei-Duplikat.

---

## 4. Mögliche Duplikate / Mehrfachnutzung

- **Eine Datei – mehrere logische Begriffe (gewollt):**
  - `icon_installation.svg` → `installation`, `wizard`
  - `icon_storage.svg` → `storage`, `backup`
  - `icon_modules.svg` → `modules`, `app-store`
  - `icon_diagnose.svg` → `diagnose`, `periphery-scan`, `monitoring`
  - `icon_help.svg` → `help`, `documentation`
  - `icon_advanced.svg` → `advanced`, `control-center`

- **Vorhandene Datei ohne AppIcon-Eintrag:**
  - `status/status_update.svg` – wird aktuell in keiner Map in `AppIcon.tsx` referenziert. Kein Duplikat, aber ungenutztes Asset.

- **Keine doppelten SVG-Dateien** in unterschiedlichen Ordnern festgestellt; jede Datei existiert genau einmal unter `frontend/public/assets/icons/`.

---

## 5. Selbstprüfung Phase 1

- **Keine neuen Funktionen entwickelt?** – Ja, nur Bestandsaufnahme.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation erstellt?** – Ja.
- **Assetstruktur websitefähig beschrieben?** – Ja, Pfad und Kategorien sind für spätere Nutzung (z. B. setuphelfer.de) referenzierbar.
