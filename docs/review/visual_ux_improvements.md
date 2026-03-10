# Visuelle UX – Verbesserungen

_Phase 8 – Visuelle Hierarchie, Statusanzeigen, Fortschritt, Orientierung_

---

## 1. Ziel

Benutzer sollen jederzeit verstehen:
- **Was passiert** (aktueller Zustand)
- **Was als nächstes kommt** (nächste Schritte, Fortschritt)

---

## 2. Visuelle Hierarchie

### Bereits umgesetzt

| Bereich | Umsetzung |
|---------|-----------|
| Seiten-Header | Einheitlich: Icon + Titel + Untertitel |
| Cards | `.card` mit Glasmorphism, konsistente Abstände |
| Modus-Tabs | Grundlagen / Erweitert / Diagnose – klare Trennung |
| Dashboard | Hero-Bereich mit Status-Badge, Ressourcen-Indikatoren |

### Verbesserungsvorschläge

| Ort | Problem | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| Installationsassistent | Schritte ohne Fortschrittsbalken | Fortschrittsbalken während Installation (bereits „X% abgeschlossen“ vorhanden) | B |
| BackupRestore | Mehrere Tabs, Orientierung | Kurzer Einleitungstext pro Tab („Hier erstellen Sie Backups…“) | C |
| ControlCenter | Viele Sektionen | Bereits Sidebar mit Kategorien – optional Gruppierung | C |

---

## 3. Statusanzeigen

### Bereits umgesetzt

- Dashboard: Status-Badge (Alles OK / Aktion benötigt / Verbindungsfehler)
- Sidebar: „Bereit“ mit status_ok Icon
- StatusItem-Komponente: aktiv (grün) / inactive (gelb)
- Backend-Fehler-Karte: Problem, Ursache, Lösung

### Verbesserungsvorschläge

| Ort | Problem | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| RunningBackupModal | Abbruch-Feedback | „Backup wird abgebrochen…“ anzeigen | B |
| InstallationWizard | Ladezustand | Bereits „Installation läuft“ + Progress – ggf. Spinner bei Schrittwechsel | C |
| Clone-Bereich | Laufender Klon | Klare Statuszeile „Klon läuft… X%“ | B |

---

## 4. Fortschrittsanzeigen

### Bereits umgesetzt

- InstallationWizard: Fortschrittsbalken (X% abgeschlossen)
- BackupRestore: RunningBackupModal mit Ergebniszeilen
- PeripheryScan: Fortschrittsbalken während Scan

### Verbesserungsvorschläge

| Ort | Problem | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| Backup-Upload | Kein detaillierter Fortschritt | Wenn API Fortschritt liefert: anzeigen | C |
| NASSetup / MusicBoxSetup | Konfiguration anwenden | „Konfiguration wird angewendet…“ (bereits teilweise) | C |

---

## 5. Orientierung

### Bereits umgesetzt

- Breadcrumbs: Keine (nicht erforderlich bei Sidebar-Navigation)
- Modus-Wechsel: Grundlagen/Erweitert/Diagnose – Nutzer wechselt Kontext
- Dokumentation: Immer im Footer erreichbar

### Verbesserungsvorschläge

| Ort | Problem | Vorschlag | Priorität |
|-----|---------|-----------|-----------|
| Modus „Erweitert“ | Unklar was „technisch“ bedeutet | Optional: Tooltip „Technische Einstellungen für erfahrene Nutzer“ | C |
| Erste Nutzung | FirstRunWizard | Bereits vorhanden – prüfen ob alle kritischen Wege abgedeckt | C |

---

## 6. Farb- und Kontrast-Konsistenz

### Statusfarben (graphics_system.md)

- Grün = OK
- Gelb = Warnung
- Rot = Fehler
- Blau = Info
- Grau = deaktiviert

### Bekannte Abweichungen (ui_consistency_report)

- PeripheryScan: emerald statt green/sky
- ControlCenter WLAN-Scan: purple statt sky
- RaspberryPiConfig Neustart: orange

→ Siehe Phase 10 (Priorisierte Nachbesserung)

---

## 7. Priorisierte Liste

### Priorität A

- (Keine visuellen A‑Probleme – Text/UX dominiert)

### Priorität B

1. RunningBackupModal: Abbruch-Feedback „Backup wird abgebrochen…“
2. Clone-Bereich: Fortschritts-/Statuszeile während Klon
3. Installationsassistent: Ggf. Spinner bei Schrittwechsel (wenn kurz verzögert)

### Priorität C

4. BackupRestore: Einleitungstext pro Tab
5. Modus-Tab „Erweitert“: Tooltip
6. ControlCenter: Optionale Kategorien-Gruppierung

---

## 8. Zusammenfassung Phase 8

Die visuelle UX ist weitgehend konsistent. Die wichtigsten Verbesserungen liegen im Feedback bei laufenden Aktionen (Abbruch, Klon-Fortschritt). Orientierung und Hierarchie sind durch Sidebar, Modus-Tabs und Cards gut gelöst.
