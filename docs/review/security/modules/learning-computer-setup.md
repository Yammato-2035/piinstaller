# Security Review: LearningComputerSetup

## Kurzbeschreibung

Lerncomputer: Status, Konfiguration. API: /api/learning/status, configure. Paketinstallation, Konfiguration.

## Angriffsfläche

Eingaben: Konfigurationsoptionen. Kritische Aktionen: apt, Konfig-Schreiben.

## Schwachstellen

Eingabe-Validierung für Konfiguration; keine Befehls-Injection.

## Empfohlene Maßnahmen

Whitelist für Optionen; sichere Befehlsaufrufe.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: /api/learning/*. frontend/src/pages/LearningComputerSetup.tsx.
