# Security Review: PresetsSetup

## Kurzbeschreibung

Voreinstellungen: Anwendung von Presets (Systemänderungen je Preset). API: Preset-bezogene Endpunkte.

## Angriffsfläche

Eingaben: Preset-ID/Auswahl. Kritische Aktionen: Systemänderungen je Preset.

## Schwachstellen

Preset-Whitelist; keine beliebigen Befehle aus Preset-Daten.

## Ampelstatus

**GELB.** Betroffene Dateien: frontend/src/pages/PresetsSetup.tsx, backend (Preset-Logik).
