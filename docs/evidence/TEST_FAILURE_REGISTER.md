# Test Failure Register

## Zweck

Dieses Register belegt, dass Testfehler und offene Testfelder explizit erfasst werden.
Ein gruener Register-Status bedeutet nur: Die Uebersicht existiert. Er bedeutet **nicht**, dass alle Tests projektweit gruen sind.

## Aktueller Fokus

- Dashboard-Green-Up-Tests fuer Runtime/Deploy/Update/Rescue/Packaging/Project-Overview
- UI-Safety-Statiktests fuer verbotene Aktionen
- Rescue-ISO-Prebuild bleibt getrennt von echtem ISO-Build

## Offene Felder

- produktive Runtime-Smokes muessen nach jedem relevanten Helper-Deploy erneut bestaetigt werden
- Backup/Restore/Live-Boot bleiben ohne neue Hardware-Evidence nicht gruen
- Packaging-Installationsabnahme bleibt pending, auch wenn Artefakte vorhanden sind
