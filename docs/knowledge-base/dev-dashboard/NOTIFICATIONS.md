# Dev Dashboard Notifications

## Unterschied Dashboard vs. E-Mail

- Dashboard-Notification: persistentes Event im Development Dashboard
- E-Mail-Notification: optionaler SMTP-Versand fuer dasselbe Event

Ein Event kann also sichtbar sein, obwohl `email_status=not_configured` oder `failed` ist.

## Wo die Daten liegen

- lokal im Workspace:
  - Event-Historie: `docs/evidence/runtime-results/notifications/notification_events.jsonl`
  - letzte Zusammenfassung: `docs/evidence/runtime-results/notifications/notification_latest_summary.json`
- produktiv unter `/opt/setuphelfer`:
  - Event-Historie: `/var/lib/setuphelfer/notifications/notification_events.jsonl`
  - letzte Zusammenfassung: `/var/lib/setuphelfer/notifications/notification_latest_summary.json`

## Wichtige Eventtypen

- `rescue_iso_build_failed`
- `deploy_helper_failed`
- `runtime_gate_failed`
- `backup_failed`
- `restore_failed`

## Rescue-ISO-Failure

Wenn der kontrollierte Rescue-ISO-Build fehlschlaegt, erzeugt das System ein persistentes Event mit:

- `LB_EXIT`
- primaerem Fehler
- ISO-Status
- USB-Status
- naechster erforderlicher Aktion

Beispiel:

- `rescue_iso_build_failed`
- `email_status=not_configured|sent|failed`

## Test-Events

Verfuegbare Dev-Dashboard-Endpunkte:

- `GET /api/dev-dashboard/notifications/status`
- `GET /api/dev-dashboard/notifications/events`
- `POST /api/dev-dashboard/notifications/test-dashboard`
- `POST /api/dev-dashboard/notifications/test-email`

## Datenschutz

- keine Secrets in Events
- keine SMTP-Passwoerter in Responses
- nur maskierte Empfaengeradresse im Dashboard

## Typische Befunde

### `email_status=not_configured`

Dashboard funktioniert, aber SMTP ist nicht vollstaendig konfiguriert.

### `email_status=failed`

Es gab einen echten Sendeversuch, aber SMTP/Auth/TLS/Netzwerk oder ein Provider-Limit ist fehlgeschlagen.

Typischer produktiver Sonderfall:

- `classification=notification.email.provider_limit_exceeded`
- `email_error=554 5.7.0 outgoing message limit exceeded`
- `next_action=check_smtp_provider_limit_or_wait`
- Dashboard bleibt **green**, E-Mail bleibt **yellow/provider_limit**
- kein automatischer Retry

### `email_status=sent`

Der Versand wurde erfolgreich abgeschlossen.
