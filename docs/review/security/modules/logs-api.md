# Security Review: Logs API

## Kurzbeschreibung

/api/logs/path, /api/logs/tail. Liefert Log-Pfad und Tail-Inhalt. Kann Path-Traversal ermöglichen, wenn Pfad aus Request kommt.

## Angriffsfläche

Eingaben: ggf. Zeilenanzahl, Pfad (wenn konfigurierbar). Kritisch: Lesen beliebiger Dateien wenn Pfad nicht fest.

## Schwachstellen

Pfad muss aus sicherer Konfiguration stammen, nicht aus Request-Parametern.

## Empfohlene Maßnahmen

Fester Log-Pfad aus Backend-Konfiguration; keine User-Parameter für Pfad.

## Ampelstatus

**GELB.** Betroffene Dateien: backend/app.py: /api/logs/*.
