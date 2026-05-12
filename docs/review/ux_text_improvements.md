# UX-Text-Verbesserungen

_Phase 3 – Buttontexte, Seitentitel, Statusmeldungen, Fehlermeldungen, Hilfetexte_

---

## 1. Regeln (ux_guidelines.md)

- Kurze Sätze, klare Aktionen, einfache Sprache
- Konsistente Begriffe: Speichern (persist), Übernehmen (sofort), Anwenden (Konfig)
- „Server“ statt „Backend“ in nutzer-sichtbaren Meldungen
- Fehlermeldungen: Problem → Ursache → Lösung

---

## 2. Buttontexte

### Verbesserungsvorschläge

| Datei | Aktuell | Vorschlag | Priorität |
|-------|---------|-----------|-----------|
| InstallationWizard.tsx | „Weiter“ | Kontext klar (Wizard) – akzeptabel | – |
| BackupRestore.tsx | confirmText: „Weiter“ (USB-Dialog) | „USB vorbereiten“ oder „Formatierung starten“ | B |
| SettingsPage.tsx | „Zurücksetzen“ | „Auf Standard zurücksetzen“ | B |
| SecuritySetup.tsx | „✓ Anwenden“ | „Sicherheitseinstellungen übernehmen“ | B |
| NASSetup.tsx | „Konfiguration anwenden“ | Beibehalten (passt zu ux_guidelines „Anwenden“) | – |
| WebServerSetup.tsx | „✓ Konfiguration anwenden“ | Beibehalten | – |
| DevelopmentEnv.tsx | „Konfigurieren“ | „Konfiguration anwenden“ (konsistent) | C |

### Bereits gut

- „Speichern“, „Übernehmen“ (ControlCenter Display/Desktop)
- „Installation jetzt starten“ (InstallationWizard)
- „Assimilation starten“ (PeripheryScan)

---

## 3. Seitentitel

### Prüfung

| Seite | Aktueller Titel | Status |
|-------|-----------------|--------|
| Dashboard | „Dashboard“ | OK |
| Einstellungen | „Einstellungen“ | OK |
| Raspberry Pi Config | „Raspberry Pi Konfiguration“ | OK (Sidebar: „Raspberry Pi Config“ – leicht inkonsistent) |
| Peripherie-Scan | „Peripherie-Scan (Assimilation)“ | „Assimilation“ technisch – optional: „Hardware-Scan“ | C |

---

## 4. Statusmeldungen

### Verbesserungsvorschläge

| Ort | Aktuell | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| Sidebar | „Bereit“ | OK | – |
| Dashboard Hero | „Alles OK“, „Aktion benötigt“, „Verbindung zum Server fehlgeschlagen“ | OK (Phase 6) | – |
| InstallationWizard | „Installation läuft“ | OK | – |
| RunningBackupModal | Laufender Job | Ggf. „Backup wird abgebrochen…“ bei Abbruch | B |
| RaspberryPiConfig | „Speichere...“ vs „Speichere…“ | Einheitliche Ellipse (drei Punkte) | C |

### Ellipsen-Konsistenz

- „Speichere…“ (Unicode …, U+2026) vs „Speichere...“ (drei Punkte)
- Empfehlung: Einheitlich „…“ (U+2026)

---

## 5. Fehlermeldungen

### Noch „Backend“ statt „Server“

| Datei | Zeile/Context | Aktuell | Vorschlag |
|-------|---------------|---------|-----------|
| SettingsPage.tsx | toast | „Backend-URL gespeichert“ | „Server-Adresse gespeichert“ |
| SettingsPage.tsx | toast | „Backend-URL zurückgesetzt“ | „Server-Adresse zurückgesetzt“ |
| PeripheryScan.tsx | toast | „Backend neu starten“ | „Server neu starten (./start-backend.sh)“ |
| BackupRestore.tsx | targetCheck | „Backend nicht erreichbar“ | „Server nicht erreichbar“ |
| BackupRestore.tsx | toast | „Backend nicht erreichbar“ | „Server nicht erreichbar“ |

### Struktur Problem → Ursache → Lösung

| Datei | Aktuell | Verbesserung |
|-------|---------|--------------|
| DsiRadioSettings.tsx | „Speichern fehlgeschlagen.“ | „Einstellungen konnten nicht gespeichert werden. Bitte Verbindung zum Server prüfen.“ |
| PresetsSetup.tsx | „Fehler beim Anwenden des Presets“ | „Voreinstellung konnte nicht übernommen werden. [Ursache wenn verfügbar].“ |
| BackupRestore.tsx | „Zeitüberschreitung. Backend nicht erreichbar…“ | „Die Aktion hat zu lange gedauert. Bitte Server prüfen oder „Ohne Prüfung speichern“ probieren.“ |
| ModulePage.tsx (Remote) | „Fehler“ | Konkrete Meldung aus Backend anzeigen |

---

## 6. Hilfetexte

### Fehlende / zu verbessernde

| Ort | Kontext | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| SettingsPage | Init-Status (Config, Device Match) | „Konfigurationsdatei:“, „Gerät passt:“; Tooltip zu Erster Start | B |
| ControlCenter | Performance (Governor, Overclocking, Swap) | Blurb: „Erweitert: Leistungs- und Speicher-Einstellungen. Nur für erfahrene Nutzer.“ | A |
| RaspberryPiConfig | Overclocking-Kategorien | HelpTooltip pro kritischer Option | B |
| MonitoringDashboard | Komponenten-Auswahl | „Wählen Sie, welche Dienste überwacht werden sollen.“ | C |

---

## 7. Technische Begriffe

| Ort | Begriff | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| SettingsPage | „Initialisierung“ | „Ersteinrichtung“ oder „Systemstatus“ | B |
| SettingsPage | „Config:“, „Device Match“ | „Konfigurationsdatei:“, „Gerät passt:“ | B |
| Dashboard | „Kernel Version“ | „Linux-Version“ | C |
| Dashboard | „API-URL“, „Genutzte API-URL“ | „Server-Adresse“ | B |
| PeripheryScan | „Assimilation“ | „Hardware-Scan“ (optional, wenn Nutzer-freundlicher) | B |

---

## 8. Priorisierte Umsetzungsliste

### Priorität A

1. ControlCenter Performance: Hilfetext/Blurb „Nur für erfahrene Nutzer“

### Priorität B

2. Backup-Dialog: confirmText „Weiter“ → „USB vorbereiten“
3. Settings „Zurücksetzen“ → „Auf Standard zurücksetzen“
4. SecuritySetup „✓ Anwenden“ → „Sicherheitseinstellungen übernehmen“
5. Restliche „Backend“-Texte → „Server“
6. DsiRadioSettings Fehlermeldung präzisieren
7. Settings Init: „Config“ → „Konfigurationsdatei“
8. Dashboard Fehler-Karte: „API-URL“ → „Server-Adresse“

### Priorität C

9. Ellipsen einheitlich (… vs ...)
10. PeripheryScan „Assimilation“ optional umbenennen
11. Raspberry Pi Config vs Konfiguration vereinheitlichen
12. DevelopmentEnv „Konfigurieren“ → „Konfiguration anwenden“
