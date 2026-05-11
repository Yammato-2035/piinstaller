# Legacy Identifier Policy

## Zweck
Aktive technische Identifier werden auf `setuphelfer` vereinheitlicht. Legacy-Identifier bleiben nur als kontrollierte, dokumentierte Kompatibilitaet erhalten.

## Aktiv verboten
- Neue `pi-installer` / `piinstaller` Runtime-Identifier
- Neue `PI_INSTALLER_*` Umgebungsvariablen
- Neue harte Pfade unter `/opt/pi-installer`
- Neue `pi-installer*.service` Runtime-Services

## Erlaubte Ausnahmen
- Historische Dokumentation
- Evidence-/Nachweisdateien
- Changelog-Historie
- Explizite Migrations- und Alias-Nachweise

## Betriebsregel
- Kein blindes Replace
- Keine automatische Runtime-Manipulation
- Keine automatischen Deletes
- Legacy wird nur kontrolliert stillgelegt und als `deprecated` markiert
