# Icon-Liste

_Dokumentation aller generierten Icons für den PI-Installer_

---

## Spezifikation

Alle Icons entsprechen dem definierten [Grafiksystem](graphics_system.md):

- **Stil:** Flache Line-Icons (Outline), minimalistisch, technisch
- **Linienstärke:** 1.5px (für 24×24 ViewBox)
- **Farben:** `currentColor` (Kontextfarbe), Statusfarben über CSS
- **Formate:** SVG, viewBox `0 0 24 24`, skalierbar

---

## Assetstruktur

```
frontend/public/assets/icons/
├── navigation/
├── status/
├── devices/
├── process/
└── diagnostic/
```

---

## Navigation (9 Icons)

| Datei | Beschreibung |
|-------|--------------|
| `icon_dashboard.svg` | Dashboard-Übersicht, vier Kacheln |
| `icon_installation.svg` | Installation, Zahnrad mit Pfeil |
| `icon_network.svg` | Netzwerk, verbundene Knoten |
| `icon_storage.svg` | Speicher, Festplatte/Laufwerk |
| `icon_modules.svg` | Module, vier Boxen |
| `icon_settings.svg` | Einstellungen, Zahnrad |
| `icon_advanced.svg` | Erweiterte Funktionen, Kreuz mit Kreisen |
| `icon_diagnose.svg` | Diagnose, Lupe mit Plus |
| `icon_help.svg` | Hilfe, Fragezeichen im Kreis |

---

## Status (8 Icons)

| Datei | Beschreibung | Empfohlene Farbe |
|-------|--------------|------------------|
| `status_ok.svg` | OK, Haken | Grün (#10b981) |
| `status_active.svg` | Aktiv, konzentrische Kreise | Grün |
| `status_running.svg` | Läuft, Play-Symbol | Blau (#3b82f6) |
| `status_warning.svg` | Warnung, Dreieck mit Ausrufezeichen | Gelb (#f59e0b) |
| `status_error.svg` | Fehler, Kreis mit X | Rot (#ef4444) |
| `status_loading.svg` | Wird geladen, Spinner | Blau |
| `status_complete.svg` | Abgeschlossen, Kreis mit Haken | Grün |
| `status_update.svg` | Update, Kreispfeil | Gelb |

---

## Geräte (9 Icons)

| Datei | Beschreibung |
|-------|--------------|
| `device_raspberrypi.svg` | Raspberry Pi, stilisierte Platine |
| `device_sdcard.svg` | SD-Karte mit Kontakten |
| `device_nvme.svg` | NVMe/SSD, M.2-Form |
| `device_usb.svg` | USB-Gerät, Stecker |
| `device_network.svg` | Netzwerk, verbundene Knoten |
| `device_wifi.svg` | WLAN, Wellen mit Punkt |
| `device_ethernet.svg` | Ethernet, Kabelstecker |
| `device_display.svg` | Display, Monitor |
| `device_audio.svg` | Audio, Lautsprecher mit Wellen |

---

## Prozess (7 Icons)

| Datei | Beschreibung |
|-------|--------------|
| `process_search.svg` | Gerät suchen, Lupe |
| `process_connect.svg` | Verbinden, Link-Kettensymbol |
| `process_prepare.svg` | Vorbereiten, Dokument |
| `process_write.svg` | Image schreiben, Upload-Pfeil |
| `process_verify.svg` | Prüfen, Haken |
| `process_restart.svg` | Neustart, Kreispfeil |
| `process_complete.svg` | Fertig, Kreis mit Haken |

---

## Diagnose (5 Icons)

| Datei | Beschreibung |
|-------|--------------|
| `diagnose_error.svg` | Fehleranalyse, Kreis mit X |
| `diagnose_logs.svg` | Logdateien, Dokument mit Zeilen |
| `diagnose_systemcheck.svg` | Systemprüfung, Haken in Dokument |
| `diagnose_debug.svg` | Debugmodus, Rahmen mit Plus |
| `diagnose_test.svg` | Testlauf, Haken |

---

## Gesamtübersicht

| Kategorie | Anzahl |
|-----------|--------|
| Navigation | 9 |
| Status | 8 |
| Geräte | 9 |
| Prozess | 7 |
| Diagnose | 5 |
| **Gesamt** | **38** |

---

## Verwendung

Icons über `currentColor` erben die Textfarbe des umgebenden Elements. Für Statusfarben CSS-Klassen setzen:

```css
.status-ok { color: #10b981; }
.status-warning { color: #f59e0b; }
.status-error { color: #ef4444; }
.status-info { color: #3b82f6; }
.status-disabled { color: #64748b; }
```
