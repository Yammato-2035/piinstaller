# Security Review: WebServerSetup

## Kurzbeschreibung

Webserver (Nginx/Apache) konfigurieren. API: status, configure. Führt systemctl, apt, Konfigurationsdateien-Schreibvorgänge aus.

## Angriffsfläche

Eingaben: Konfigurationsoptionen, ggf. Domain/VHost. Kritische Aktionen: Schreiben von Config-Dateien, systemctl reload.

## Schwachstellen

Konfig-Inhalte aus Request: Validierung nötig, um Injection (z. B. in Nginx-Config) zu verhindern.

## Empfohlene Maßnahmen

Template-basierte Konfig mit whitelisteten Variablen; keine Roh-Request-Bodies in Config-Dateien.

## Ampelstatus

**GELB.**

## Betroffene Dateien

backend/app.py: /api/webserver/*. frontend/src/pages/WebServerSetup.tsx. backend/modules/webserver.py.
