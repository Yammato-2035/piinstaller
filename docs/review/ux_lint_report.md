# UX Lint Report

_Automatische UX-Qualitätsprüfung – Analyse ohne Code-Änderungen_

---

## 1. Zusammenfassung

| Kategorie | Anzahl | Priorität A | Priorität B | Priorität C |
|-----------|--------|-------------|-------------|-------------|
| Unklare Buttons | 4 | 1 | 2 | 1 |
| Technische Begriffe | 12 | 3 | 6 | 3 |
| Inkonsistente Begriffe | 5 | 1 | 2 | 2 |
| Fehlermeldungen | 8 | 2 | 4 | 2 |
| Fehlende Statusanzeigen | 3 | 1 | 2 | 0 |
| Fehlende Hilfetexte | 6 | 0 | 4 | 2 |
| Navigation | 2 | 0 | 1 | 1 |
| Überfüllte Screens | 4 | 1 | 2 | 1 |
| Einsteigerprobleme | 5 | 2 | 2 | 1 |

---

## 2. Unklare Buttons

| Datei | Stelle | Aktueller Text | Vorschlag | Priorität |
|-------|--------|----------------|-----------|-----------|
| `InstallationWizard.tsx` | ~357 | „Weiter“ | „Weiter zum nächsten Schritt“ (bei mehrdeutigem Kontext) | C |
| `FirstRunWizard.tsx` | ~97, 196 | „Weiter“ | Akzeptabel – Wizard-Kontext klar | – |
| `BackupRestore.tsx` | 542 | confirmText: „Weiter“ | „USB vorbereiten“ oder „Formatierung starten“ (Dialog-Kontext) | B |
| `SettingsPage.tsx` | 552 | „Zurücksetzen“ | „Auf Standard zurücksetzen“ (bei API-URL) | B |
| `SecuritySetup.tsx` | 358 | „✓ Anwenden“ | „Sicherheitseinstellungen übernehmen“ – eindeutiger | B |

---

## 3. Technische Begriffe

| Datei | Begriff | Kontext | Vorschlag | Priorität |
|-------|---------|---------|-----------|-----------|
| `SettingsPage.tsx` | „Initialisierung“ | Abschnittstitel | „Ersteinrichtung“ oder „Systemstatus“ | B |
| `SettingsPage.tsx` | „Config:“, „Device Match“ | Init-Status | „Konfigurationsdatei:“, „Gerät passt:“ | B |
| `ControlCenter.tsx` | „Interface“ | WiFi-Status | „Netzwerkschnittstelle“ oder weglassen | C |
| `ControlCenter.tsx` | „xrandr“, „DISPLAY“, „X-Session“ | Display-Hinweis | Kurze Erklärung: „Bildschirm-Konfiguration (nur bei laufender Grafikumgebung)“ | A |
| `ControlCenter.tsx` | „Daemon starten“, „ckb-next-daemon“ | Corsair/Hinweis | „Hintergrunddienst starten“ + Befehl | B |
| `ControlCenter.tsx` | „Kernel 6.13+“, „Kernel-Treiber“ | Corsair-Info | „Ab Linux-Version 6.13“ – oder in Doku auslagern | B |
| `ControlCenter.tsx` | „CPU-Governor“, „Overclocking“, „Swap“, „config.txt“, „dphys-swapfile“ | Performance | Tooltip: „Erweitert: Leistungs- und Speicher-Einstellungen. Nur für erfahrene Nutzer.“ | A |
| `RaspberryPiConfig.tsx` | „config.txt“, „GPU-Memory“, „Overclocking“ | Diverse | Bereits im Erweitert-Bereich; zusätzlicher Hinweis für Anfänger | B |
| `Dashboard.tsx` | „Kernel Version“ | Systeminfo | „Linux-Version“ | C |
| `Dashboard.tsx` | „API-URL“, „Genutzte API-URL“ | Fehler-Karte | „Server-Adresse“ (konsistent mit Phase 6) | B |
| `PeripheryScan.tsx` | „Assimilation“ | Begriff im Scan | „Hardware-Scan“ oder „Suche starten“ (wenn noch sichtbar) | B |
| `Documentation.tsx` | Viele (Backend, API, Kernel, etc.) | Doku | Akzeptabel – Zielgruppe dort technikaffin | – |

---

## 4. Inkonsistente Begriffe

| Problem | Fundstellen | Einheitlicher Begriff | Priorität |
|---------|-------------|------------------------|-----------|
| „Speichern“ vs. „Übernehmen“ vs. „Anwenden“ | ControlCenter: „Übernehmen“ (Display), „Speichern“ (Tastatur); SecuritySetup: „Anwenden“; NASSetup: „Konfiguration anwenden“ | Siehe ux_guidelines: Speichern (persist), Übernehmen (sofort), Anwenden (Konfig) – aber Nutzer unterscheiden evtl. nicht | B |
| „Backend“ vs. „Server“ | Phase 6 hat viele auf „Server“ umgestellt; Settings/Toast noch vereinzelt „Backend“ | Durchgängig „Server“ in Nutzer-sichtbaren Texten | B |
| „Config“ vs. „Konfiguration“ | RaspberryPiConfig, Settings „Config:“ | „Konfiguration“ in Beschriftungen | C |
| „Neu laden“ vs. „Aktualisieren“ | Settings, RaspberryPiConfig: „Neu laden“ | Einheitlich „Aktualisieren“ oder „Neu laden“ (beides ok, nur konsistent) | C |
| „Konfigurieren“ vs. „Konfiguration anwenden“ | NASSetup: „Konfiguration anwenden“; DevelopmentEnv: „Konfigurieren“ | „Einstellungen übernehmen“ oder „Konfiguration speichern“ | C |

---

## 5. Fehlermeldungen

| Datei | Aktuell | Verbesserung | Priorität |
|-------|---------|--------------|-----------|
| `DsiRadioSettings.tsx` | „Speichern fehlgeschlagen.“ | „Einstellungen konnten nicht gespeichert werden. Bitte Verbindung prüfen.“ | B |
| `DevelopmentEnv.tsx` | „Diese Funktion ist derzeit nicht verfügbar.“ | „Diese Funktion wird noch entwickelt. Bitte nutzen Sie die Dokumentation für manuelle Schritte.“ | B |
| `ModulePage.tsx` (Remote) | „Fehler“ | Konkretere Meldung aus Backend anzeigen | C |
| `BackupRestore.tsx` | „Zeitüberschreitung. Backend nicht erreichbar oder sudo-Prüfung hängt.“ | „Die Aktion hat zu lange gedauert. Server prüfen oder „Ohne Prüfung speichern“ probieren.“ | B |
| `BackupRestore.tsx` | „Externe Backups konnten nicht geladen werden (Backend nicht erreichbar)“ | „Cloud-Backups konnten nicht geladen werden. Server nicht erreichbar.“ | C |
| `PeripheryScan.tsx` | Console: „> Fehler: Backend nicht erreichbar.“ | „> Der Server ist nicht erreichbar. Bitte starten Sie ihn (./start-backend.sh).“ | B |
| `PresetsSetup.tsx` | „Fehler beim Anwenden des Presets“ | „Voreinstellung konnte nicht übernommen werden. [Ursache aus Backend].“ | C |
| Diverse | „Fehler beim X“ (generisch) | Wo möglich: konkrete Ursache + kurzer Lösungshinweis | B |

---

## 6. Fehlende Statusanzeigen

| Ort | Problem | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| `InstallationWizard` | Kein Fortschrittsbalken während Installation | „Installation läuft…“ + Fortschritt oder Ladeindikator | A |
| `BackupRestore` | Während Backup/Clone: Statusmodal existiert, aber „Abbruch“-Feedback | Klare Meldung „Backup wird abgebrochen…“ | B |
| `MusicBoxSetup`, `NASSetup` | „Konfigurieren“-Ladezustand | „Konfiguration wird angewendet…“ – teilweise vorhanden, prüfen ob überall | B |
| `RunningBackupModal` | Laufender Job – Fortschritt | Bereits vorhanden; ggf. Prozentangabe deutlicher | C |

---

## 7. Fehlende Hilfetexte

| Datei | Option/Einstellung | Vorschlag | Priorität |
|-------|--------------------|-----------|-----------|
| `SettingsPage` | „Erster Start“, „Device Match“ | Tooltip: „ja = Erstinstallation; nein = System wurde schon eingerichtet“ | B |
| `ControlCenter` | Performance: Governor, GPU-Memory, Swap | Kurzer Blurb: „Für erfahrene Nutzer. Änderungen können Neustart erfordern.“ | A |
| `RaspberryPiConfig` | Overclocking-Optionen | HelpTooltip pro Kategorie | B |
| `BackupRestore` | Verschlüsselung, Cloud-Modi | Kurze Erklärung, was „GPG“ vs. „OpenSSL“ bedeutet | B |
| `MonitoringDashboard` | Komponenten-Auswahl | „Wählen Sie, welche Dienste überwacht werden sollen.“ | C |
| `SecuritySetup` | Fail2Ban, SSH-Hardening | Einzeiler was es bewirkt (teilweise vorhanden) | C |

---

## 8. Navigation

| Problem | Fundstelle | Vorschlag | Priorität |
|---------|------------|-----------|-----------|
| Modus-Tabs „Grundlagen | Erweitert | Diagnose“ | Sidebar | Optional: Kurzer Hinweis unter „Erweitert“: „Technische Einstellungen“ | C |
| „Peripherie-Scan“ vs. „Assimilation“ | Früher Assimilation im Namen | Bereits auf „Peripherie-Scan“ vereinfacht (Phase 5) | – |
| Dokumentation-Link im Footer | Immer sichtbar | Gut – keine Änderung | – |

---

## 9. Überfüllte Screens

| Screen | Problem | Vorschlag | Priorität |
|--------|---------|-----------|-----------|
| `ControlCenter` | Viele Bereiche (WLAN, SSH, VNC, Display, Performance, Lüfter, RGB, …) | Bereits Toggle „Erweiterte Optionen“; ggf. Kategorien (Netzwerk, Anzeige, Erweitert) | B |
| `RaspberryPiConfig` | Viele Kategorien, Overclocking, EDID, Overlays | Bereits im Erweitert-Bereich; Kategorien gruppieren | B |
| `BackupRestore` | Tabs Backup, Einstellungen, Wiederherstellen, Klonen; viele Optionen | Struktur ok; Einleitungstext pro Tab könnte Orientierung geben | B |
| `SettingsPage` | Allgemein, Cloud, Logs; Init, Netzwerk, Basic, Screenshots | „Initialisierung“-Begriff vereinfachen (s. oben) | A |

---

## 10. Einsteigerprobleme

| Risiko | Beschreibung | Priorität |
|--------|---------------|-----------|
| **Sudo-Dialog beim ersten Start** | Nutzer verstehen evtl. nicht, wofür sudo benötigt wird | A |
| **„Server nicht erreichbar“** | Bereits verbessert (Phase 6); „./start-backend.sh“ ist für Einsteiger trotzdem technisch | A |
| **Control Center Performance** | Governor, Swap, Overclocking – hohes Fehlbedienungsrisiko | A |
| **Backup-Verschlüsselung** | GPG/OpenSSL ohne Erklärung – Einsteiger überfordert | B |
| **Raspberry Pi Config** | config.txt-Änderungen können System unbootbar machen | B |
| **InstallationWizard** | Schritte evtl. nicht klar genug erklärt | B |

---

## Priorisierte Verbesserungsliste

### Priorität A – kritisch für Anfänger

1. **Control Center Performance:** Hilfetext/Blurb „Nur für erfahrene Nutzer. Änderungen können Neustart erfordern.“
2. **InstallationWizard:** Klare Fortschritts-/Statusmeldung während Installation.
3. **SettingsPage „Initialisierung“:** Verständlichere Bezeichnung (z.B. „Ersteinrichtung“).
4. **Control Center Display:** Erklärung für „xrandr nicht erreichbar“ (ohne X-Session) – Anfänger verstehen „DISPLAY“ nicht.
5. **Sudo-Dialog:** Optionaler Hinweis „Wird für Installationen und Sicherheitseinstellungen benötigt.“

### Priorität B – Verbesserung sinnvoll

6. **Fehlermeldungen:** „Backend“ durchgängig durch „Server“ ersetzen (Restbestände).
7. **Button „Anwenden“ in SecuritySetup:** Konkreter machen („Sicherheitseinstellungen übernehmen“).
8. **DsiRadioSettings Fehler:** Konkretere Meldung statt nur „Speichern fehlgeschlagen“.
9. **BackupRestore Timeout:** Formulierung nutzerfreundlicher.
10. **PeripheryScan Console:** „Backend“ → „Server“ in Fehlermeldung.
11. **Assimilation/technische Begriffe:** Wo sichtbar, vereinfachen oder mit Tooltip versehen.
12. **Settings „Zurücksetzen“:** „Auf Standard zurücksetzen“ bei API-URL.

### Priorität C – kosmetisch

13. **„Weiter“ in Dialogen:** Wo Kontext unklar, spezifischer (z.B. „Formatierung starten“).
14. **„Config“ vs. „Konfiguration“:** Einheitlich „Konfiguration“.
15. **ModulePage Remote:** Konkretere Fehlermeldung aus Backend.

---

## Die 15 wichtigsten UX-Probleme im Projekt

1. **Control Center Performance/Overclocking** – Expertenoptionen ohne deutlichen Warnhinweis.
2. **Sudo-Dialog** – Einsteiger verstehen „Administrator-Rechte“ evtl. nicht im Kontext.
3. **„Server nicht erreichbar“ + ./start-backend.sh** – Technisch für absolute Einsteiger.
4. **InstallationWizard** – Fehlende oder unklare Statusanzeige während Installation.
5. **Settings „Initialisierung“** – Technischer Begriff für Ersteinrichtung.
6. **Control Center Display** – „xrandr“, „DISPLAY“, „X-Session“ ohne Erklärung.
7. **Inkonsistenz Speichern/Übernehmen/Anwenden** – Drei Begriffe für ähnliche Aktionen.
8. **BackupRestore** – Verschlüsselung (GPG/OpenSSL) ohne Einsteiger-Erklärung.
9. **Raspberry Pi Config** – Viele Low-Level-Optionen, Risiko Fehlbedienung.
10. **Fehlermeldungen** – Teilweise noch „Backend“ statt „Server“.
11. **DsiRadioSettings** – Generische „Speichern fehlgeschlagen“-Meldung.
12. **SecuritySetup „Anwenden“** – Könnte konkreter sein.
13. **BackupRestore Timeout** – Lange technische Fehlermeldung.
14. **PeripheryScan** – Console „Backend nicht erreichbar“.
15. **HelpTooltip-Abdeckung** – Nicht alle technischen Optionen haben Hilfetexte.
