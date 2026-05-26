# Notification Email Setup Runbook

## Ziel

SMTP fuer Setuphelfer-Notifications konfigurieren, ohne Secrets ins Repo oder in API-Responses zu schreiben.

## Konfigurationsdatei

- Laufzeitdatei: `/etc/setuphelfer/notification.env`
- Service-Drop-in: `packaging/systemd/setuphelfer-backend.service.d/notification-env.conf.example`

## Verwendete Variablen

- `SETUPHELFER_NOTIFY_EMAIL_ENABLED`
- `SETUPHELFER_NOTIFY_EMAIL_TO`
- `SETUPHELFER_NOTIFY_EMAIL_FROM`
- `SETUPHELFER_NOTIFY_SMTP_HOST`
- `SETUPHELFER_NOTIFY_SMTP_PORT`
- `SETUPHELFER_NOTIFY_SMTP_USERNAME`
- `SETUPHELFER_NOTIFY_SMTP_PASSWORD`
- `SETUPHELFER_NOTIFY_SMTP_SECURITY`
- `SETUPHELFER_NOTIFY_SMTP_STARTTLS`
- `SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS`
- `SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE`

## Beispielablauf

1. Drop-in installieren:

```bash
sudo cp packaging/systemd/setuphelfer-backend.service.d/notification-env.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/notification-env.conf
```

2. `notification.env` anlegen:

```bash
sudo install -o root -g setuphelfer -m 660 /dev/null /etc/setuphelfer/notification.env
sudoedit /etc/setuphelfer/notification.env
```

3. Minimalbeispiel:

```env
SETUPHELFER_NOTIFY_EMAIL_ENABLED=true
SETUPHELFER_NOTIFY_EMAIL_TO=operator@example.com
SETUPHELFER_NOTIFY_EMAIL_FROM=setuphelfer@example.com
SETUPHELFER_NOTIFY_SMTP_HOST=smtp.example.com
SETUPHELFER_NOTIFY_SMTP_PORT=587
SETUPHELFER_NOTIFY_SMTP_USERNAME=setuphelfer@example.com
SETUPHELFER_NOTIFY_SMTP_PASSWORD=<secret>
SETUPHELFER_NOTIFY_SMTP_SECURITY=starttls
SETUPHELFER_NOTIFY_SMTP_STARTTLS=true
```

4. Service neu laden:

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
```

## Validierung

- Settings UI: `/api/settings/notifications/email`
- Dev-Dashboard-Status: `/api/dev-dashboard/notifications/status`
- Testmail: `POST /api/dev-dashboard/notifications/test-email`

## Wichtige Regeln

- `.env` oder `notification.env` niemals committen
- kein SMTP-Passwort in Logs oder Evidence kopieren
- `sent` nur dann akzeptieren, wenn der Endpunkt echten Versand meldet
- `not_configured` bedeutet: Dashboard kann trotzdem funktionieren, aber E-Mail nicht

## Troubleshooting

### SMTP fehlt

- `email_status=not_configured`
- Host, Port, Empfaenger, Absender und Passwort pruefen

### Falscher Empfaenger

- `SETUPHELFER_NOTIFY_EMAIL_TO` pruefen
- im Dashboard wird nur die maskierte Adresse angezeigt

### Auth fehlgeschlagen

- Benutzername / Passwort / Absender pruefen
- `email_status=failed`

### Netzwerk blockiert

- SMTP-Host / Port / Firewall / DNS pruefen
- `email_status=failed`

### Provider-Limit / Versandkontingent erreicht

- `email_status=failed`
- `email_error` auf Provider-Hinweise wie `554 5.7.0` oder `limit on the number of allowed outgoing messages was exceeded` pruefen
- nach Provider-Window erneut testen; Dashboard-Events bleiben davon unabhaengig sichtbar

### Event erzeugt, aber keine Mail

- Dashboard-Eventliste pruefen
- `email_status` und `email_error` auswerten
- `not_configured` ist kein Versandfehler, sondern Konfigurationsluecke
