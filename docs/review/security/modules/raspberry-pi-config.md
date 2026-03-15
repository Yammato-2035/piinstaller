# Security Review: RaspberryPiConfig

## Kurzbeschreibung

Raspberry-Pi-spezifische Konfiguration (raspi-config-Äquivalent). Nur auf Pi sichtbar. API: systembezogene Schreibvorgänge.

## Angriffsfläche

Eingaben: Konfig-Optionen. Kritische Aktionen: systemctl, Konfig-Dateien. Modul raspberry_pi_config.py.

## Schwachstellen

Validierung der Konfig-Werte; keine Befehls-Injection.

## Ampelstatus

**GRÜN** bei whitelisteter Konfiguration. Betroffene Dateien: backend/modules/raspberry_pi_config.py, app.py, frontend/src/pages/RaspberryPiConfig.tsx.
