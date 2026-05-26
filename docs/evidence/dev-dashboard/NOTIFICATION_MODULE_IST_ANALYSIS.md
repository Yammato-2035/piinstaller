# Notification Module IST Analysis

**Datum:** 2026-05-25  
**Scope:** Rescue-ISO-Failure, Development Dashboard, E-Mail-Benachrichtigungen  
**Status:** `ANALYZED`

## Ausgangsbefund

Die Ausgangslage vor der Reparatur zeigte einen teilweisen Notification-Stack, aber **keine** allgemeine Dev-Dashboard-Notification-Pipeline fuer Rescue-/Deploy-/Runtime-Fehler.

OpenAPI-Befund vor der Erweiterung:

- vorhanden: `/api/settings/notifications/email`
- vorhanden: `/api/settings/notifications/email/test`
- nicht vorhanden: `/api/dev-dashboard/notifications/status`
- nicht vorhanden: `/api/dev-dashboard/notifications/events`
- nicht vorhanden: `/api/dev-dashboard/notifications/test-dashboard`
- nicht vorhanden: `/api/dev-dashboard/notifications/test-email`

## Tabelle

| Bereich | Befund | Datei/Endpoint | Status | Problem |
|---|---|---|---|---|
| Backend API | Nur Settings-/Testmail-Endpunkte vorhanden | `backend/app.py`, `/api/settings/notifications/email`, `/api/settings/notifications/email/test` | incomplete | Kein Dev-Dashboard-API-Contract fuer persistente Notifications |
| Backend Event-Erzeugung | Backup-bezogene E-Mail-Erzeugung vorhanden | `backend/core/notification_service.py`, `backend/tools/backup_runner.py` | incomplete | Rescue-/Deploy-/Runtime-Failures erzeugen kein allgemeines Notification-Event |
| Event-Persistenz | Nur Konfiguration und Test-Meta werden persistiert | `backend/core/notification_settings.py`, `notification_email_test_meta.json` | missing | Keine Eventliste, keine JSONL-Historie, keine Dashboard-lesbare Failure-Persistenz |
| Dashboard-Anzeige | Keine Notification-Komponente im Dev-Dashboard | `frontend/src/pages/DevelopmentDashboard.tsx`, `frontend/src/pages/ExternalDevelopmentControlCenter.tsx` | missing | Rescue-Failure konnte im Cockpit nicht als Event angezeigt werden |
| E-Mail-Konfiguration | SMTP-/Empfaenger-Konfiguration vorhanden | `backend/core/notification_settings.py`, `frontend/src/pages/SettingsPage.tsx` | present | Konfig existiert, ist aber nur an Backup-/Testmail-Flows angebunden |
| SMTP/Sendmail | SMTP-Senden vorhanden | `backend/core/notification_service.py` | present | Generischer Event-Versand ausserhalb Backup fehlte |
| Fehlerzustellung | Backup-Fehler koennen E-Mails ausloesen | `backend/tests/test_backup_failure_notification_v1.py` | incomplete | Rescue-ISO-Failure wurde nicht an denselben Kanal angebunden |
| Retry/Queue | Keine Queue gefunden | kein Treffer in `backend`, `frontend`, `docs` | missing | Keine warteschlangenbasierte Zustellung, keine Retry-Strategie |
| Tests | Settings-/Backup-Notification-Tests vorhanden | `backend/tests/test_notification_service_v1.py`, `backend/tests/test_notification_settings_api_v1.py`, `backend/tests/test_backup_failure_notification_v1.py` | incomplete | Keine Tests fuer allgemeine Dashboard-Events und Rescue-Failure-Notifications |
| i18n DE/EN | Keine Dev-Dashboard-Notification-Texte vorhanden | `frontend/src/locales/de.json`, `frontend/src/locales/en.json` | incomplete | Keine UI-Texte fuer Event-Liste, E-Mail-Status und Notification-Panel |
| Doku | Backup-Notification-Doku vorhanden | `docs/operations/BACKUP_NOTIFICATIONS_RUNTIME_DE.md`, `docs/backup/BACKUP_NOTIFICATIONS_DE.md`, `docs/backup/BACKUP_NOTIFICATIONS_EN.md` | incomplete | Keine allgemeine Notification-Doku fuer Dev-Dashboard/Rescue |
| FAQ | Keine dedizierte Notification-FAQ gefunden | `docs/faq/` | missing | Kein FAQ fuer Dashboard vs. E-Mail, SMTP-Probleme, not_configured |
| Wissensdatenbank | Kein Dev-Dashboard-Notification-Artikel gefunden | `docs/knowledge-base/` | missing | Kein KB-Eintrag zu Event-Persistenz, Test-Event, Rescue-Failure-Sichtbarkeit |

## Warum vorher keine Dashboard-Meldung kam

Belastbare Ursache:

- Es gab **keine** allgemeinen `/api/dev-dashboard/notifications/*`-Endpunkte.
- Es gab **keine** persistente Eventliste fuer Dashboard-Notifications.
- Es gab **keine** Notification-Komponente im Development Dashboard.
- Die vorhandene Notification-Logik war auf Backup-Resultate begrenzt.

## Warum vorher keine E-Mail kam

Belastbare Ursache:

- Es existierte zwar SMTP-/E-Mail-Konfiguration, aber **keine** Anbindung des Eventtyps `rescue_iso_build_failed`.
- Der Rescue-ISO-Failure wurde nur in Summary/Evidence/Logs sichtbar, nicht in einen allgemeinen Notification-Event uebersetzt.
- Damit konnte der bestehende Mail-Versandpfad fuer Backup-Benachrichtigungen nicht greifen.

## Fazit

Vor der Reparatur war das System in diesem Punkt nicht "kaputt im SMTP-Sinn", sondern funktional unvollstaendig:

- **Settings vorhanden**
- **Backup-Mailpfad vorhanden**
- **allgemeine Dashboard-/Rescue-Notifications fehlten**

Genau diese Luecke wurde im aktuellen Scope geschlossen.
