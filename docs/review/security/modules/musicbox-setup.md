# Security Review: MusicBoxSetup

## Kurzbeschreibung

Musikbox (Mopidy): Status, Diagnose, Konfiguration. API: /api/musicbox/status, mopidy-diagnose, configure.

## Angriffsfläche

Eingaben: Konfigurationsdaten. Kritische Aktionen: apt, systemctl, Konfig-Dateien.

## Schwachstellen

Konfig-Validierung: Keine gefährlichen Werte (Pfade, URLs) ungeprüft in Config schreiben.

## Empfohlene Maßnahmen

Validierung vor Schreibvorgängen; Template/Whitelist.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: /api/musicbox/*. frontend/src/pages/MusicBoxSetup.tsx.
