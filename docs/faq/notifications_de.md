# FAQ Notifications (DE)

## Warum sehe ich ein Event im Dashboard, aber keine E-Mail?

Weil Dashboard und E-Mail getrennt bewertet werden. Ein Event kann korrekt persistiert und sichtbar sein, obwohl SMTP nicht konfiguriert ist oder der Versand fehlgeschlagen ist.

## Was bedeutet `not_configured`?

SMTP-/Empfaenger-Konfiguration ist nicht vollstaendig genug fuer einen echten Versand.

## Was bedeutet `failed`?

Ein echter Versand wurde versucht, ist aber fehlgeschlagen. Details stehen redigiert in `email_error`.

## Wo finde ich die Event-Historie?

- lokal im Workspace:
  - `docs/evidence/runtime-results/notifications/notification_events.jsonl`
  - `docs/evidence/runtime-results/notifications/notification_latest_summary.json`
- produktiv unter `/opt/setuphelfer`:
  - `/var/lib/setuphelfer/notifications/notification_events.jsonl`
  - `/var/lib/setuphelfer/notifications/notification_latest_summary.json`

## Wie erzeuge ich ein Test-Event?

- Dashboard-Test: `POST /api/dev-dashboard/notifications/test-dashboard`
- Test-E-Mail: `POST /api/dev-dashboard/notifications/test-email`

## Warum kam der Rescue-ISO-Failure frueher nicht als Notification an?

Weil vorher nur Backup-bezogene E-Mail-Logik existierte und kein allgemeiner Dev-Dashboard-Notification-Stack fuer Rescue-Failures vorhanden war.
