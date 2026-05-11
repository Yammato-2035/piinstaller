# Security Review: MailServerSetup

## Kurzbeschreibung

Mailserver-Konfiguration. developerOnly. API: Mail-bezogene Endpunkte (backend/modules/mail.py). Konfiguration, ggf. Paketinstallation.

## Angriffsfläche

Eingaben: Mail-Konfiguration (Domain, Credentials). Credentials nicht loggen.

## Ampelstatus

**GRÜN** (developerOnly). Betroffene Dateien: backend/modules/mail.py, app.py, frontend/src/pages/MailServerSetup.tsx.
