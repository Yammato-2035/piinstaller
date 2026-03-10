# UX Guidelines

_Phase 6 – UX-Optimierung für Anfänger_

## 1. Zielgruppe

Linux- und Raspberry-Pi-Einsteiger sowie fortgeschrittene Nutzer. Die Oberfläche soll für Anfänger verständlich sein, ohne Expertenfunktionen zu verstecken.

---

## 2. UX-Prinzipien

- **Klare Sprache:** Kurze Sätze, aktive Form, einfache Wörter
- **Einfache Aktionen:** Buttons beschreiben genau, was passiert
- **Sichtbarer Status:** Nutzer sieht jederzeit, was läuft und ob etwas funktioniert
- **Verständliche Fehlermeldungen:** Problem, mögliche Ursache, Lösung
- **Wenig technische Begriffe:** Nur wo nötig (z.B. Backend in Fehlermeldungen, da Nutzer danach suchen)
- **Konsistente Farben:** Grün = OK, Gelb = Warnung, Rot = Fehler, Blau = Info

---

## 3. UI-Begriffe (einheitlich)

| Begriff | Verwendung | Nicht verwenden |
|---------|------------|-----------------|
| **Speichern** | Einstellungen dauerhaft speichern | Save, Commit |
| **Übernehmen** | Änderungen sofort anwenden (Display, Boot) | Apply, Submit |
| **Anwenden** | Konfiguration aktivieren | Apply, Execute |
| **Starten** | Prozess/Installation beginnen | Run, Execute |
| **Installation** | Einrichtung/Vorgang | Setup, Deploy |
| **Status** | Aktueller Zustand | State |
| **Einstellungen** | Konfiguration | Settings (in UI deutsch) |
| **Diagnose** | Fehlersuche, Systemanalyse | Debug (für Nutzer) |
| **Backend** | Server-Komponente (bei Fehlern) | API, Server (kann ergänzt werden) |

---

## 4. Fehlermeldungsstruktur

**Toast (kurz):**
1. Was ist schiefgelaufen?
2. Kurzer Hinweis zur Lösung (wenn Platz)

**Beispiel:**
- Statt: `Connection failed`
- Besser: `Verbindung fehlgeschlagen. Bitte Backend starten (./start-backend.sh).`

**Karte/Dialog (ausführlich):**
1. **Problem:** Was ist passiert?
2. **Ursache:** Mögliche Gründe (z.B. Backend läuft nicht)
3. **Lösung:** Konkrete Schritte (z.B. Backend starten, Einstellungen prüfen)

---

## 5. Statusbegriffe

| Status | Bedeutung |
|--------|-----------|
| Bereit | System wartet auf Aktion |
| Aktiv | Vorgang läuft |
| Wird vorbereitet | Initialisierung |
| Läuft | Prozess aktiv |
| Abgeschlossen | Erfolgreich beendet |
| Warnung | Achtung, Prüfung empfohlen |
| Fehler | Etwas ist schiefgelaufen |

Vermeiden: Technische Statuscodes (HTTP, Exit-Codes) in der UI.

---

## 6. Buttons – Regeln

- **Aktive Sprache:** „Installation starten“, nicht „Start“
- **Klare Aktion:** Maximal 3–4 Wörter
- **Kein "OK" allein:** Stattdessen die Aktion nennen („Speichern“, „Schließen“)

---

## 7. Hilfetexte

Technische Optionen erhalten kurze Erklärungen:
- Tooltip (title/Hover)
- Beschreibung unter der Option
- HelpTooltip (wo vorhanden)

**Beispiel:**
- Label: „Debugmodus“
- Hilfetext: „Aktiviert zusätzliche Diagnoseinformationen für die Fehlersuche.“

---

## 8. Grundlagenbereich

Enthält nur:
- Häufig genutzte Funktionen
- Sichere Einstellungen
- Statusinformationen

Enthält nicht (→ Erweiterte Funktionen):
- Entwickleroptionen
- Debugsteuerung
- Hardware-Tuning
- Experimentelle Funktionen
