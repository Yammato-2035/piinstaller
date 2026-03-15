# Security Review: Dashboard

## Kurzbeschreibung

Startseite: Systeminfo, Services-Status, Ressourcen. Nur Lese-API (system-info, dashboard/services-status, system/resources).

## Angriffsfläche

Eingaben: Keine kritischen. Ausgaben: Systeminformationen (Hostname, Kernel, Speicher, Dienste).

## Schwachstellen

Keine kritischen. Information Disclosure begrenzt (keine Passwörter, nur für Admin-UI gedacht).

## Empfohlene Maßnahmen

Keine zusätzlichen. Sensible Infos (z. B. interne IPs) akzeptabel im LAN-Kontext.

## Ampelstatus

**GRÜN.**

## Betroffene Dateien

backend/app.py: /api/system-info, /api/dashboard/services-status, /api/system/resources. frontend/src/pages/Dashboard.tsx.
