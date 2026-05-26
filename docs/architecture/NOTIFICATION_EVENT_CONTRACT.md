# Notification Event Contract

**Status:** `active`  
**Scope:** Development Dashboard + E-Mail-Benachrichtigungen

## Ziel

Dashboard-Notifications und E-Mail-Benachrichtigungen werden ueber denselben persistenten Event-Vertrag beschrieben. Ein Event darf im Dashboard sichtbar sein, auch wenn keine E-Mail konfiguriert ist oder kein Versand stattfindet.

## Pflicht-Eventtypen

- `rescue_iso_build_failed`
- `rescue_iso_build_success`
- `rescue_usb_write_blocked`
- `rescue_usb_write_started`
- `rescue_usb_write_failed`
- `rescue_usb_write_success`
- `runtime_gate_failed`
- `deploy_helper_failed`
- `deploy_helper_success`
- `backup_failed`
- `backup_success`
- `restore_blocked`
- `restore_failed`
- `restore_success`

Hinweis:

- fuer Smoke-/Selftest-Endpunkte sind zusaetzlich Test-Eventtypen wie `notification_test_dashboard` und `notification_test_email` erlaubt

## Pflichtfelder

```json
{
  "event_id": "...",
  "created_at": "...",
  "severity": "info|warning|error|critical",
  "area": "rescue|runtime|deploy|backup|restore|packaging",
  "event_type": "...",
  "title": "...",
  "message": "...",
  "technical_summary": "...",
  "evidence_paths": [],
  "dashboard_visible": true,
  "email_requested": true,
  "email_status": "not_configured|queued|sent|failed|disabled",
  "email_error": null,
  "acknowledged": false
}
```

## Regeln

1. Dashboard-Notification darf auch ohne E-Mail funktionieren.
2. `email_status=sent` ist nur zulaessig, wenn ein echter SMTP-Versand erfolgreich abgeschlossen wurde.
3. `not_configured` ist **kein** Erfolg und darf nicht als `sent` gemeldet werden.
4. Failure-Events muessen persistent gespeichert werden.
5. Keine Secrets in `title`, `message`, `technical_summary` oder `email_error`.
6. Empfaengeradresse und SMTP-Zugangsdaten kommen aus Konfiguration, nicht aus hart codierten Werten.
7. Test-Ereignisse duerfen `email_requested=false` setzen und damit `email_status=disabled` erhalten.

## Persistenz

Pfadregeln:

- Workspace-/lokaler Testpfad:
  - `docs/evidence/runtime-results/notifications/notification_events.jsonl`
  - `docs/evidence/runtime-results/notifications/notification_latest_summary.json`
- produktiver `/opt`-Runtime-Pfad:
  - `/var/lib/setuphelfer/notifications/notification_events.jsonl`
  - `/var/lib/setuphelfer/notifications/notification_latest_summary.json`

## E-Mail-Semantik

- `disabled`: E-Mail fuer dieses Event bewusst nicht angefordert oder global deaktiviert
- `not_configured`: SMTP-/Empfaenger-Konfiguration unvollstaendig
- `queued`: reserviert fuer spaetere Queue/Retry-Strategien
- `sent`: echter Versand erfolgreich
- `failed`: Versand versucht, aber fehlgeschlagen; `email_error` redigiert

## Datenschutz

- keine SMTP-Passwoerter in Events
- keine Tokens in Events
- nur maskierte Empfaengeradresse in Status-/Response-Payloads
