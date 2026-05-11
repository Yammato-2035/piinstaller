# Security Review: PeripheryScan

## Kurzbeschreibung

Peripherie-Scan: Hardware erkennen. API: /api/peripherals/scan. Lese-Operationen, evtl. USB/udev.

## Angriffsfläche

Eingaben: Keine. Ausgabe: Geräteliste.

## Schwachstellen

Keine kritischen. Keine Schreib- oder Install-Aktionen.

## Ampelstatus

**GRÜN.**

## Betroffene Dateien

backend/app.py: /api/peripherals/scan. frontend/src/pages/PeripheryScan.tsx.
