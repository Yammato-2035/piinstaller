# Security Review: ControlCenter

## Kurzbeschreibung

Control Center: WLAN, Display, Bluetooth. API nutzt wpa_cli, ddccontrol, rfkill über run_command.

## Angriffsfläche

Eingaben: WLAN-SSID/Passwort, Display-Einstellungen. Kritische Aktionen: systemnahe Befehle.

## Schwachstellen

WPA-Passphrase und Parameter: Keine Roh-Strings in Shell; Validierung SSID/Passphrase.

## Empfohlene Maßnahmen

Befehle aus Listen/Whitelist; WPA-Passphrase nicht loggen.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: Control-Center-relevante Routen. backend/modules/control_center.py. frontend/src/pages/ControlCenter.tsx.
