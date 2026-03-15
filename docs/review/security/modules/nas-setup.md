# Security Review: NASSetup

## Kurzbeschreibung

NAS-Status, Konfiguration, Duplikate-Scan/Install, move-to-backup. API: /api/nas/status, configure, duplicates/*. Pfade und Dateioperationen.

## Angriffsfläche

Eingaben: Pfade, Ziele. Kritische Aktionen: mount, move, scan über Verzeichnisse.

## Schwachstellen

Path Traversal: Alle Pfade strikt validieren (realpath, Unterpfad erlaubter Basis).

## Empfohlene Maßnahmen

Pfad-Whitelist; keine relativen Pfade aus Request direkt verwenden.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: /api/nas/*. frontend/src/pages/NASSetup.tsx.
