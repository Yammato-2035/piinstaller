# Graphics System

_Vollständiges und konsistentes Grafiksystem für PI-Installer_

---

## 1. Ziel des Grafiksystems

- **Einheitliches Erscheinungsbild** über alle Bereiche der Anwendung
- **Klar erkennbare Statuskommunikation** für Einsteiger und Experten
- **Technisch-freundlicher Stil** – modern, minimalistisch, professionell
- **Einfache Integration** durch klare Struktur und Benennung

Die Grafiken unterstützen:

- Navigation und Orientierung
- Statusanzeigen (bereit, aktiv, Fehler, Warnung)
- Installationsabläufe (Schritte, Fortschritt)
- Gerätestatus (verbunden, erkannt)
- Diagnose (Logs, Prüfung)
- Leere Zustände (kein Gerät, keine Daten)
- Hilfebereiche

---

## 2. Icon-Stil

| Eigenschaft | Spezifikation |
|-------------|---------------|
| **Stil** | Flache Line-Icons (Outline) |
| **Form** | Klare, minimalistische Formen |
| **Kanten** | Leicht gerundet (stroke-linecap: round, stroke-linejoin: round) |
| **Komplexität** | Maximal 2–3 zusammengehörige Elemente pro Icon |
| **Details** | Keine Schatten, keine Verläufe, keine 3D-Effekte |

**Referenz:** Ähnlich Lucide Icons / Feather Icons – aber einheitlich für PI-Installer definiert.

---

## 3. Farbpalette

### Primärfarben

| Name | Hex | Verwendung |
|------|-----|------------|
| **Sky (Primär)** | `#0284c7` | Akzente, aktive Zustände, Links |
| **Sky Light** | `#0ea5e9` | Hover, Highlights |
| **Slate Dark** | `#1e293b` | Hintergründe (Dark Mode) |
| **Slate Light** | `#94a3b8` | Text sekundär |
| **White** | `#ffffff` | Icons auf dunklem Hintergrund |

### Statusfarben

| Status | Hex | Verwendung |
|--------|-----|------------|
| **OK / Aktiv** | `#10b981` | Alles in Ordnung, verbunden |
| **Warnung** | `#f59e0b` | Aufmerksamkeit, Update verfügbar |
| **Fehler** | `#ef4444` | Fehler, getrennt, Abbruch |
| **Information** | `#3b82f6` | Hinweise, Info-Dialoge |
| **Deaktiviert** | `#64748b` | Inaktiv, ausgegraut |

### Icon-Farben

- **Standard:** `currentColor` – erbt von Text/Kontext
- **Status-Icons:** Primär Sky oder Statusfarben (grün/gelb/rot/blau)
- **Maximal zwei Farben** pro Icon (Outline + optional Akzent)

---

## 4. Linienstärke & Größen

### Linienstärke

| Größe | Stroke-Width |
|-------|--------------|
| 16px, 24px | 1.5px |
| 32px | 2px |
| 48px, 64px | 2.5px |

Einheitliche Linienstärke innerhalb einer Icon-Größe.

### Icongrößen

| Größe | Verwendung |
|-------|------------|
| **16px** | Inline mit Text, kleine Badges |
| **24px** | Buttons, Listen, Menü |
| **32px** | Karten-Header, Überschriften |
| **48px** | Leere Zustände, große Aktionen |
| **64px** | Willkommens-Screens, Illustrationen |

### Bevorzugtes Format

**SVG** – skalierbar, leichtgewichtig, editierbar.

---

## 5. Icon-Kategorien

### 5.1 Navigation Icons

| ID | Name | Datei | Beschreibung |
|----|------|-------|--------------|
| nav_dashboard | Dashboard | `icon_nav_dashboard.svg` | Übersicht, Tachometer/Grid |
| nav_install | Installation | `icon_nav_install.svg` | Zahnrad + Pfeil, Assistent |
| nav_network | Netzwerk | `icon_nav_network.svg` | WLAN-Symbol |
| nav_storage | Speicher | `icon_nav_storage.svg` | Festplatte/Database |
| nav_status | Systemstatus | `icon_nav_status.svg` | Activity/Pulse |
| nav_modules | Module | `icon_nav_modules.svg` | Puzzleteil oder Boxen |
| nav_settings | Einstellungen | `icon_nav_settings.svg` | Zahnrad |
| nav_advanced | Erweiterte Funktionen | `icon_nav_advanced.svg` | Schraubenschlüssel/Sliders |
| nav_diagnose | Diagnose | `icon_nav_diagnose.svg` | Lupe oder Bug |
| nav_help | Hilfe | `icon_nav_help.svg` | Buch, Fragezeichen |

### 5.2 Status Icons

| ID | Name | Datei | Farbe | Beschreibung |
|----|------|-------|-------|--------------|
| status_ready | Bereit | `icon_status_ready.svg` | Grau | Kreis leer, wartend |
| status_active | Aktiv | `icon_status_active.svg` | Grün | Kreis gefüllt, Punkt |
| status_running | Läuft | `icon_status_running.svg` | Blau | Animierter Indikator (Spinner) |
| status_connected | Verbunden | `icon_status_connected.svg` | Grün | Verbindungslinie durchgezogen |
| status_disconnected | Getrennt | `icon_status_disconnected.svg` | Rot | Verbindungslinie unterbrochen |
| status_warning | Warnung | `icon_status_warning.svg` | Gelb | Dreieck mit Ausrufezeichen |
| status_error | Fehler | `icon_status_error.svg` | Rot | Kreis mit X |
| status_done | Abgeschlossen | `icon_status_done.svg` | Grün | Haken |
| status_loading | Wird geladen | `icon_status_loading.svg` | Blau | Spinner/Puls |
| status_update | Update verfügbar | `icon_status_update.svg` | Gelb | Pfeil nach oben, Download |

### 5.3 Geräte-Icons

| ID | Name | Datei | Beschreibung |
|----|------|-------|--------------|
| device_raspberrypi | Raspberry Pi | `icon_device_raspberrypi.svg` | Stilisierter Pi (Raspberry-Logo-Orientierung) |
| device_sdcard | SD-Karte | `icon_device_sdcard.svg` | Rechteck mit Kontakten |
| device_nvme | NVMe/SSD | `icon_device_nvme.svg` | M.2-Form, schlank |
| device_usb | USB-Gerät | `icon_device_usb.svg` | USB-Symbol |
| device_network | Netzwerk | `icon_device_network.svg` | Verbundene Knoten |
| device_wifi | WLAN | `icon_device_wifi.svg` | WLAN-Bogen |
| device_ethernet | Ethernet | `icon_device_ethernet.svg` | Kabel/Stecker |
| device_display | Display | `icon_device_display.svg` | Monitor |
| device_audio | Audio | `icon_device_audio.svg` | Lautsprecher/Waveform |

### 5.4 Prozess-Icons (Installation)

| ID | Name | Datei | Beschreibung |
|----|------|-------|--------------|
| process_search | Gerät suchen | `icon_process_search.svg` | Lupe + Gerät |
| process_found | Gerät gefunden | `icon_process_found.svg` | Checkmark + Gerät |
| process_connect | Verbinden | `icon_process_connect.svg` | Zwei verbindende Punkte |
| process_prepare | Vorbereiten | `icon_process_prepare.svg` | Zahnrad + Uhr |
| process_write | Image schreiben | `icon_process_write.svg` | Stift/Schreiben |
| process_verify | Prüfen | `icon_process_verify.svg` | Lupe + Check |
| process_reboot | Neustart | `icon_process_reboot.svg` | Kreispfeil |
| process_done | Fertig | `icon_process_done.svg` | Großer Haken |

### 5.5 Diagnose-Icons

| ID | Name | Datei | Beschreibung |
|----|------|-------|--------------|
| diag_error | Fehleranalyse | `icon_diag_error.svg` | Lupe + Fehlersymbol |
| diag_log | Logdateien | `icon_diag_log.svg` | Dokument mit Zeilen |
| diag_check | Systemprüfung | `icon_diag_check.svg` | Checkliste |
| diag_debug | Debugmodus | `icon_diag_debug.svg` | Bug/Käfer |
| diag_test | Testlauf | `icon_diag_test.svg` | Play + Check |

### 5.6 Leere Zustände (Illustrationen)

| ID | Name | Datei | Beschreibung |
|----|------|-------|--------------|
| empty_no_device | Kein Gerät | `illus_empty_no_device.svg` | Leerer Stecker/Raspi-Umriss |
| empty_no_modules | Keine Module | `illus_empty_no_modules.svg` | Leere Boxen/Regal |
| empty_no_errors | Keine Fehler | `illus_empty_no_errors.svg` | Check + leere Liste |
| empty_no_network | Kein Netzwerk | `illus_empty_no_network.svg` | Durchgestrichenes WLAN |

---

## 6. Assetstruktur

```
frontend/public/
  assets/
    icons/
      navigation/          # icon_nav_*.svg
      status/              # icon_status_*.svg
      devices/             # icon_device_*.svg
      process/             # icon_process_*.svg
      diagnostic/          # icon_diag_*.svg
    illustrations/
      install/             # illus_install_*.svg
      connect/             # illus_connect_*.svg
      diagnose/            # illus_diagnose_*.svg
      empty_states/        # illus_empty_*.svg
```

---

## 7. Dateinamenregeln

| Muster | Beispiel | Kategorie |
|--------|----------|-----------|
| `icon_nav_<name>.svg` | `icon_nav_dashboard.svg` | Navigation |
| `icon_status_<name>.svg` | `icon_status_ok.svg` | Status |
| `icon_device_<name>.svg` | `icon_device_raspberrypi.svg` | Geräte |
| `icon_process_<name>.svg` | `icon_process_install.svg` | Prozess |
| `icon_diag_<name>.svg` | `icon_diag_log.svg` | Diagnose |
| `illus_<category>_<name>.svg` | `illus_empty_no_device.svg` | Illustrationen |

Kleinschreibung, Unterstriche, keine Leerzeichen.

---

## 8. Icon-Regeln

1. **Maximal zwei Farben** – Outline + optional Akzent
2. **Keine komplexen Details** – bei 16px noch erkennbar
3. **Konsistente Perspektive** – vorzugsweise 2D, von vorn
4. **Gleiche Linienstärke** innerhalb einer Größenstufe
5. **ViewBox:** `0 0 24 24` für Standard-Icons (skalierbar)
6. **stroke** statt fill für Outline-Icons; `fill="none"` für Hintergrund
7. **currentColor** nutzen, wo Farbe vom Kontext kommt

---

## 9. Illustrationsregeln

1. **Leicht technisch** – Boards, Kabel, Screens andeuten
2. **Raspberry-Pi-Bezug** – wo sinnvoll (z.B. leeres Gerät)
3. **Minimalistisch** – wenige Formen, klare Silhouetten
4. **Maximal drei Farben** – Primär, Sekundär, Hintergrund
5. **Klare Formen** – keine fotorealistischen Details
6. **Keine Comicoptik** – sachlich, freundlich
7. **Typische Größe:** 200×200px bis 400×400px ViewBox

---

## 10. Vollständige Grafikliste

### Navigation (10)

- icon_nav_dashboard
- icon_nav_install
- icon_nav_network
- icon_nav_storage
- icon_nav_status
- icon_nav_modules
- icon_nav_settings
- icon_nav_advanced
- icon_nav_diagnose
- icon_nav_help

### Status (10)

- icon_status_ready
- icon_status_active
- icon_status_running
- icon_status_connected
- icon_status_disconnected
- icon_status_warning
- icon_status_error
- icon_status_done
- icon_status_loading
- icon_status_update

### Geräte (9)

- icon_device_raspberrypi
- icon_device_sdcard
- icon_device_nvme
- icon_device_usb
- icon_device_network
- icon_device_wifi
- icon_device_ethernet
- icon_device_display
- icon_device_audio

### Prozess (8)

- icon_process_search
- icon_process_found
- icon_process_connect
- icon_process_prepare
- icon_process_write
- icon_process_verify
- icon_process_reboot
- icon_process_done

### Diagnose (5)

- icon_diag_error
- icon_diag_log
- icon_diag_check
- icon_diag_debug
- icon_diag_test

### Leere Zustände (4)

- illus_empty_no_device
- illus_empty_no_modules
- illus_empty_no_errors
- illus_empty_no_network

**Gesamt: 46 Grafiken**

---

## 11. Integrationsplan

### Dashboard

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Status-Badge | status_active, status_warning, status_error |
| Ressourcen (CPU, RAM, Speicher) | device_* (optional) oder Status-Farben |
| Quick Actions | icon_nav_*, icon_process_* |
| Backend-Fehler | illus_empty_no_network oder status_disconnected |

### Installation / Assistent

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Schritte | icon_process_prepare, icon_process_write, icon_process_verify |
| Fortschritt | status_running, status_done |
| Abschluss | icon_process_done |

### Einstellungen

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Tabs | icon_nav_settings, icon_diag_log |
| Verbindung | status_connected, status_disconnected |

### Backup & Restore

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Tabs | icon_nav_storage |
| Laufwerk | icon_device_sdcard, icon_device_nvme |
| Prozess | icon_process_write, status_running |

### Control Center

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Bereiche | icon_device_wifi, icon_device_display, icon_device_audio |
| Status | status_active, status_ready |

### Raspberry Pi Config

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Header | icon_device_raspberrypi |
| Kategorien | icon_nav_* je Kategorie |

### Peripherie-Scan / Diagnose

| Bereich | Icons/Illustrationen |
|---------|----------------------|
| Scan | icon_process_search, icon_process_found |
| Geräte | icon_device_* |
| Logs | icon_diag_log |

### Leere Zustände (generisch)

| Kontext | Illustration |
|---------|--------------|
| Kein Gerät verbunden | illus_empty_no_device |
| Keine Apps/Module | illus_empty_no_modules |
| Keine Fehler | illus_empty_no_errors |
| Kein Netzwerk | illus_empty_no_network |

---

## 12. Abschlussbericht

### Definiertes Designsystem

- **Icon-Stil:** Flache Line-Icons, 1.5–2.5px Stroke, leicht gerundet
- **Farbpalette:** Sky (#0284c7) Primär; Status Grün/Gelb/Rot/Blau/Grau
- **Format:** SVG, ViewBox 24×24 Standard
- **Größen:** 16, 24, 32, 48, 64px

### Vollständige Iconliste

- **46 Grafiken** in 6 Kategorien
- Navigation: 10, Status: 10, Geräte: 9, Prozess: 8, Diagnose: 5, Leere Zustände: 4

### Assetstruktur

```
frontend/public/assets/
  icons/{navigation,status,devices,process,diagnostic}/
  illustrations/{install,connect,diagnose,empty_states}/
```

### Integrationsplan

- Dashboard, Installation, Einstellungen, Backup, Control Center, Raspberry Pi Config, Peripherie-Scan, Leere Zustände
- Klare Zuordnung: welche Icons auf welchen Screens

### Nächste Schritte (nicht Teil dieses Auftrags)

1. SVG-Assets gemäß Spezifikation erstellen
2. Ordnerstruktur `frontend/public/assets/` anlegen
3. Icons schrittweise in Komponenten integrieren (optional, Ersatz für lucide-react)
4. Illustrations für leere Zustände einbinden
