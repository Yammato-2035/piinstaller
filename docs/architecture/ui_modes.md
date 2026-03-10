# UI Modes – Grundlagen, Erweiterte Funktionen, Diagnose

_Informationsarchitektur: Einsteiger, Experten, Diagnose_

## 1. Ziel der Trennung

- **Einsteiger** sehen nur häufig genutzte, sichere Funktionen.
- **Experten** haben vollen Zugriff auf technische Einstellungen.
- **Diagnose** bündelt Fehlersuche und Systemanalyse.
- Keine Funktion geht verloren – alles bleibt erreichbar.

---

## 2. Grundlagenbereich

| Funktion | Seite | Zielgruppe | Begründung |
|----------|-------|------------|------------|
| Dashboard | dashboard | Alle | Übersicht, Status, schnelle Aktionen |
| Assistent | wizard | Einsteiger | Geführte Erstinstallation |
| Voreinstellungen | presets | Einsteiger | Schnelle Konfigurationsprofile |
| Einstellungen | settings | Alle | Basis-Konfiguration, Netzwerk, API-URL |
| Sicherheit | security | Alle | Grundlegende Sicherheitseinstellungen |
| Benutzer | users | Alle | Benutzerverwaltung |
| Backup & Restore | backup | Alle | Lokales Sichern/Wiederherstellen |
| App Store | app-store | Alle | App-Installation |
| PI-Installer Update | pi-installer-update | Alle | Update-Check |
| DSI-Radio Einstellungen | dsi-radio-settings | Freenove-Nutzer | Hauptfunktion auf Freenove-TFT |

**Dokumentation** ist im Footer immer erreichbar.

---

## 3. Erweiterte Funktionen

| Funktion | Seite | Zielgruppe | Technische Beschreibung |
|----------|-------|------------|-------------------------|
| Linux Companion | remote | Experten | Fernzugriff, Pairing (QR), Geräte |
| Dev-Umgebung | devenv | Entwickler | Entwicklungsumgebung (aktuell nicht verfügbar) |
| Webserver | webserver | Admins | Webserver-Konfiguration |
| Mailserver | mailserver | Admins | Mail-Konfiguration (aktuell nicht verfügbar) |
| NAS | nas | Admins | NAS-Setup |
| Hausautomatisierung | homeautomation | Fortgeschrittene | Smart Home |
| Musikbox | musicbox | Fortgeschrittene | Musik-Setup |
| Kino / Streaming | kino-streaming | Fortgeschrittene | Streaming-Konfiguration |
| Lerncomputer | learning | Pädagogen | Lern-Setup |
| Monitoring | monitoring | Admins | Systemüberwachung |
| Control Center | control-center | Experten | WLAN, SSH, VNC, Display, Performance, Lüfter, RGB |
| Peripherie-Scan | periphery-scan | Experten | Hardware-Erkennung |
| Raspberry Pi Config | raspberry-pi-config | Pi-Admins | Overclocking, EDID, Overlays, UART |
| DSI-Radio Einstellungen | dsi-radio-settings | Alle (wenn Freenove) | Auch in Erweitert sichtbar |

---

## 4. Entwickler-/Diagnosebereich

| Funktion | Seite | Zweck |
|----------|-------|-------|
| Einstellungen | settings | Tab „Logs“: Systemprotokolle |
| Monitoring | monitoring | Systemstatus, Sensoren, Ressourcen |
| Peripherie-Scan | periphery-scan | Hardware-Scan, Assimilation |

**Hinweis:** Für System-Logs: Einstellungen → Tab „Logs“ wählen.

---

## 5. Entscheidungsregeln

| Kriterium | Grundlagen | Erweitert |
|-----------|------------|-----------|
| Nutzungshäufigkeit | häufig | selten |
| Fehlerrisiko | gering | mittel bis hoch |
| Technischer Anspruch | niedrig | hoch |
| Typische Aktion | Einrichtung, Status, Update | Konfiguration, Tuning |
| Zielgruppe | Einsteiger, Alltagsnutzer | Admins, Experten |

| Kriterium | Diagnose |
|-----------|----------|
| Zweck | Fehlersuche, Systemanalyse |
| Inhalt | Logs, Monitoring, Hardware-Scan |
| Zielgruppe | Support, Entwickler |

---

## 6. Technische Umsetzung

- **UIModeContext:** Speichert Modus (basic | advanced | diagnose), persistiert in localStorage.
- **Sidebar:** Drei Tabs (Grundlagen | Erweitert | Diagnose), filtert Menüeinträge nach Modus.
- **Control Center:** Toggle „Erweiterte Optionen“ blendet Performance, ASUS ROG Lüfter, Corsair/RGB ein.
- **Settings:** Bestehender Toggle „Erweiterte Einstellungen“ für Basic/Screenshots-Tabs.

---

## 7. Vollständige Screen–Kategorie–Zuordnung

| Page-ID | Screen | Kategorie | Begründung |
|---------|--------|-----------|------------|
| dashboard | Dashboard | Grundlagen | Übersicht, Einstieg |
| remote | Linux Companion | Erweitert | Fernzugriff, QR-Pairing |
| app-store | App Store | Grundlagen | App-Installation, häufig |
| dsi-radio-settings | DSI-Radio Einstellungen | Grundlagen + Erweitert | Freenove-spezifisch |
| wizard | Assistent | Grundlagen | Geführte Installation |
| presets | Voreinstellungen | Grundlagen | Schnelle Profile |
| settings | Einstellungen | Grundlagen + Diagnose | Basis + Logs-Tab |
| security | Sicherheit | Grundlagen | Basis-Sicherheit |
| users | Benutzer | Grundlagen | Benutzerverwaltung |
| devenv | Dev-Umgebung | Erweitert | Entwicklungstools |
| webserver | Webserver | Erweitert | Admin-Konfiguration |
| mailserver | Mailserver | Erweitert | Admin-Konfiguration |
| nas | NAS | Erweitert | NAS-Setup |
| homeautomation | Hausautomatisierung | Erweitert | Smart Home |
| musicbox | Musikbox | Erweitert | Musik-Setup |
| kino-streaming | Kino / Streaming | Erweitert | Streaming |
| learning | Lerncomputer | Erweitert | Pädagogik |
| monitoring | Monitoring | Erweitert + Diagnose | Systemüberwachung |
| backup | Backup & Restore | Grundlagen | Sichern/Wiederherstellen |
| pi-installer-update | PI-Installer Update | Grundlagen | Update-Check |
| control-center | Control Center | Erweitert | WLAN, SSH, VNC, Display, etc. |
| periphery-scan | Peripherie-Scan | Erweitert + Diagnose | Hardware-Erkennung |
| raspberry-pi-config | Raspberry Pi Config | Erweitert | Pi-spezifisch, Overclocking |
| documentation | Dokumentation | – | Footer, immer erreichbar |

---

## 8. Keine Funktion verloren

Alle Funktionen bleiben erreichbar. Aus dem Grundlagenbereich entfernte Einträge erscheinen im Erweitert-Bereich. Der Modus-Wechsel ist jederzeit möglich.

---

## 9. Abweichungen / Hinweise

- **documentation** und **tft** sind nicht in der Sidebar (Dokumentation über Footer-Button, TFT über URL-Parameter).
- **raspberry-pi-config** wird nur angezeigt, wenn `isRaspberryPi` true ist.
