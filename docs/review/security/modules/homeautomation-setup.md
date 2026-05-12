# Security Review: HomeAutomationSetup

## Kurzbeschreibung

Hausautomatisierung: Status, Suche, Uninstall, Konfiguration. API: /api/homeautomation/status, search, uninstall, configure. Paketinstallation, systemctl.

## Angriffsfläche

Eingaben: Suchbegriffe, Konfiguration, Paket-/Komponenten-IDs.

## Schwachstellen

Eingaben in Befehle (apt, Konfig): Nur whitelistete Werte verwenden; keine freien Strings in shell.

## Empfohlene Maßnahmen

Whitelist für Aktionen und Paketnamen; Listen-Argumente für subprocess.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: /api/homeautomation/*. frontend/src/pages/HomeAutomationSetup.tsx.
