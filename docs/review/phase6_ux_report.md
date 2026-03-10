# Phase 6 – UX-Optimierung für Anfänger

_Datum: 2026-03-09_

## Abschlussbericht

### 1. Verbesserte Fehlermeldungen

| Ort | Vorher | Nachher |
|-----|--------|---------|
| Dashboard Status | "Backend nicht erreichbar" | "Verbindung zum Server fehlgeschlagen" |
| Dashboard Karte | Technische Formulierungen | Klarere Ursachen (Timeout, Verbindung) + "Lösung:" vor den Schritten |
| SudoPasswordDialog | "Backend nicht erreichbar" + technische Anleitung | "Der Server antwortet nicht" + konkrete Schritte (./start-backend.sh) |
| UserManagement | "Backend erreichbar?" | "Speichern fehlgeschlagen. Bitte starten Sie den Server (./start-backend.sh)..." |
| SettingsPage | "Backend nicht erreichbar" in Toasts | "Server nicht erreichbar – bitte Backend starten und erneut versuchen" |
| ControlCenter | "(Backend nicht erreichbar)" in Toasts | "Server nicht erreichbar." |
| App.tsx (DSI Radio) | "Backend nicht erreichbar" / "Backend OK" | "Server nicht erreichbar" / "Server bereit" |

### 2. Neue Hilfetexte

- **Settings „Verbindung zum Server“:** Überschrift von "Backend-Verbindung" zu "Verbindung zum Server", Beschreibung vereinfacht.
- **Dashboard:** Fehlermeldung mit Struktur Problem → Ursache → Lösung.

### 3. Vereinheitlichte Begriffe

- **Server** statt **Backend** in nutzer sichtbaren Meldungen (Dashboard, Sudo-Dialog, Toasts).
- **Backend** bleibt in der Dokumentation (Suchbegriff für fortgeschrittene Nutzer).
- **Speichern / Übernehmen / Anwenden** in ux_guidelines.md definiert.

### 4. Klarere Statusmeldungen

- "Verbindung zum Server fehlgeschlagen" statt "Backend nicht erreichbar" im Status-Label.
- "Server bereit" statt "Backend OK" im DSI-Radio-Tooltip.

### 5. Verbesserte Navigation/Orientierung

- Keine Änderung der Navigation (Phase 5).
- Fehlermeldungen verweisen klar auf "Lösung:" und konkrete Befehle.

---

## Die 10 wichtigsten UX-Verbesserungen

1. **Dashboard:** Aussagekräftigerer Fehlerstatus „Verbindung zum Server fehlgeschlagen“.
2. **Dashboard:** Fehlermeldung mit Problem, Ursache und Lösung.
3. **SudoPasswordDialog:** Verständlichere Meldung „Der Server antwortet nicht“ mit konkreter Handlungsanleitung.
4. **Toasts:** „Server nicht erreichbar“ statt „Backend nicht erreichbar“ (einheitlicher, verständlicher).
5. **Settings:** Bereich „Verbindung zum Server“ mit klarerer Beschreibung.
6. **UserManagement:** Präzisere Timeout- und Verbindungsfehler-Meldungen.
7. **ux_guidelines.md:** Zentrale UX-Regeln, Begriffe, Fehlerstruktur.
8. **Konsistenz:** Server/Bereit-Status in App, Dashboard und Toasts vereinheitlicht.
9. **Aktive Sprache:** „Der Server antwortet nicht“, „Bitte starten Sie den Server“.
10. **Lösungsorientierung:** Fehlermeldungen nennen konkrete Schritte (./start-backend.sh).
