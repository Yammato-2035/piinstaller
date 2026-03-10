# Icon-Verwendung in der UI

_Dokumentation aller UI-Bereiche und verwendeter Icons_

---

## Übersicht

Icons werden über die Komponente `AppIcon` (`frontend/src/components/AppIcon.tsx`) eingebunden.  
Basis: `frontend/public/assets/icons/` (SVG-Dateien).

---

## 1. Navigation (Sidebar)

| UI-Element | Icon | Größe | Datei |
|------------|------|-------|-------|
| Dashboard | icon_dashboard | 24px | navigation/icon_dashboard.svg |
| App Store | icon_modules | 24px | navigation/icon_modules.svg |
| Assistent | icon_installation | 24px | navigation/icon_installation.svg |
| Einstellungen | icon_settings | 24px | navigation/icon_settings.svg |
| Monitoring | icon_diagnose | 24px | navigation/icon_diagnose.svg |
| Backup & Restore | icon_storage | 24px | navigation/icon_storage.svg |
| Control Center | icon_advanced | 24px | navigation/icon_advanced.svg |
| Peripherie-Scan | icon_diagnose | 24px | navigation/icon_diagnose.svg |
| Dokumentation | icon_help | 24px | navigation/icon_help.svg |
| Tab Grundlagen | icon_dashboard | 16px | navigation/icon_dashboard.svg |
| Tab Erweitert | icon_advanced | 16px | navigation/icon_advanced.svg |
| Tab Diagnose | icon_diagnose | 16px | navigation/icon_diagnose.svg |

---

## 2. Statusanzeigen

| UI-Bereich | Kontext | Icon | Größe | Datei |
|------------|---------|------|-------|-------|
| Sidebar Footer | System bereit | status_ok | 16px | status/status_ok.svg |
| Dashboard Hero | Alles OK | status_ok | 20px | status/status_ok.svg |
| Dashboard Hero | Aktion benötigt | status_warning | 20px | status/status_warning.svg |
| Dashboard Hero | Verbindungsfehler | status_error | 20px | status/status_error.svg |
| Dashboard | Installation Status (Überschrift) | status_complete | 24px | status/status_complete.svg |
| Dashboard | StatusItem (aktiv) | status_ok | 20px | status/status_ok.svg |
| Dashboard | StatusItem (inaktiv) | status_warning | 20px | status/status_warning.svg |
| Dashboard | Backend-Fehler Karte | status_error | 24px | status/status_error.svg |
| InstallationWizard | Installation läuft | status_running | 24px | status/status_running.svg |

---

## 3. Seiten-Header

| Seite | Icon | Größe | Datei |
|-------|------|-------|-------|
| Dashboard | icon_dashboard | 32px | navigation/icon_dashboard.svg |
| Installationsassistent | icon_installation | 32px | navigation/icon_installation.svg |
| Einstellungen | icon_settings | 32px | navigation/icon_settings.svg |
| Peripherie-Scan | icon_diagnose | 32px | navigation/icon_diagnose.svg |
| Raspberry Pi Konfiguration | device_raspberrypi | 32px | devices/device_raspberrypi.svg |

---

## 4. Geräteanzeigen

| UI-Bereich | Icon | Größe | Datei |
|------------|------|-------|-------|
| Control Center – WLAN | device_wifi | 32px | devices/device_wifi.svg |
| Control Center – Display | device_display | 32px | devices/device_display.svg |
| Backup & Restore – USB / Datenträger | device_usb | 24px | devices/device_usb.svg |

---

## 5. Installationsablauf (Prozess)

| Schritt/UI | Icon | Größe | Datei |
|------------|------|-------|-------|
| Assistent – Schritt 1 Willkommen | process_connect | 48px | process/process_connect.svg |
| Assistent – Schritte 2–5 | process_prepare | 48px | process/process_prepare.svg |
| Assistent – Schritt 6 Zusammenfassung | process_complete | 48px | process/process_complete.svg |
| Peripherie-Scan – Assimilation starten | process_search | 24px | process/process_search.svg |

---

## 6. Diagnose

| UI-Bereich | Icon | Größe | Datei |
|------------|------|-------|-------|
| Einstellungen – Logs Tab | diagnose_logs | 18px | diagnostic/diagnose_logs.svg |

---

## 7. Nicht integrierte Icons (für zukünftige Nutzung)

Folgende Icons sind vorhanden, werden aktuell aber noch nicht in der UI verwendet:

- **Navigation:** icon_network (für Netzwerk-Bereiche)
- **Status:** status_loading, status_active, status_update
- **Geräte:** device_sdcard, device_nvme, device_network, device_ethernet, device_audio
- **Prozess:** process_write, process_verify, process_restart
- **Diagnose:** diagnose_error, diagnose_systemcheck, diagnose_debug, diagnose_test

---

## 8. AppIcon-Komponente

### Verwendung

```tsx
import AppIcon from '../components/AppIcon'

// Navigation (24px Standard)
<AppIcon name="dashboard" category="navigation" size={24} />

// Status mit Farbe
<AppIcon name="ok" category="status" size={20} statusColor="ok" />
<AppIcon name="warning" category="status" size={20} statusColor="warning" />
<AppIcon name="error" category="status" size={24} statusColor="error" />

// Geräte
<AppIcon name="wifi" category="devices" size={32} />
<AppIcon name="usb" category="devices" size={24} />

// Prozess
<AppIcon name="search" category="process" size={48} />

// Diagnose
<AppIcon name="logs" category="diagnostic" size={18} />
```

### statusColor (nur für category="status")

- `ok` – Grün (#10b981)
- `warning` – Gelb (#f59e0b)
- `error` – Rot (#ef4444)
- `info` – Blau (#3b82f6)
- `muted` – Grau (#64748b)

---

## 9. Validierung

- [x] UI startet korrekt
- [x] Navigation funktioniert
- [x] Icons laden unter `/assets/icons/`
- [x] Layout bleibt stabil
- [x] Keine Backend-/Konfigurationslogik verändert
