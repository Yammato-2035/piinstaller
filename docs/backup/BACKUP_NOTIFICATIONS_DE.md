# Backup-Erfolg: E-Mail-Benachrichtigungen

## Wann wird eine E-Mail gesendet?

Nur nach abgeschlossenem Backup-Job mit:

- **`backup.success`**, oder
- **`backup.success_with_warnings`** mit **`backup_integrity_status: verified`** und erfolgreichem **Verify Deep** im Runner

Nicht bei `backup.failed`, `backup.warning_not_promoted`, fehlendem Archiv oder ungültigem Verify.

## Warum nur nach erfolgreichem Verify (bei Warnungen)?

BR-001 und die Integritätskette verlangen ein finales Archiv, SHA256 und Verify Deep. Die Benachrichtigung darf keinen „Erfolg“ suggerieren, wenn die Kette nicht bestanden wurde.

## Konfiguration über die UI

Unter **Einstellungen → E-Mail-Benachrichtigungen** können Empfänger, SMTP-Daten und das Mailbox-Passwort gesetzt werden. Das Passwort wird **nicht** angezeigt und nicht in API-Antworten zurückgegeben (`smtp_password_set` nur true/false). Mit **Testmail senden** prüfen Sie SMTP ohne Backup.

**Verschlüsselung (`smtp_security`):**

| Modus | Typischer Port | Verhalten |
|-------|----------------|-----------|
| `starttls` | 587 | `SMTP` + `STARTTLS` |
| `ssl` | 465 | `SMTP_SSL` (implizites TLS) |
| `none` | 25 o. ä. | unverschlüsselt |

Ohne `SETUPHELFER_NOTIFY_SMTP_SECURITY`: Port **465** → `ssl`, sonst `smtp_starttls=true` → `starttls`.

## Konfiguration (Umgebungsvariablen)

Umgebungsvariablen (siehe `.env.example`):

| Variable | Bedeutung |
|----------|-----------|
| `SETUPHELFER_NOTIFY_EMAIL_ENABLED` | `true` zum Aktivieren |
| `SETUPHELFER_NOTIFY_EMAIL_TO` | Empfänger |
| `SETUPHELFER_NOTIFY_EMAIL_FROM` | Absender |
| `SETUPHELFER_NOTIFY_SMTP_*` | SMTP-Server, Port, Zugangsdaten |
| `SETUPHELFER_NOTIFY_SMTP_SECURITY` | `starttls`, `ssl` oder `none` |
| `SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS` | Standard `true` |

Secrets nur in `.env` (gitignored) oder systemd `EnvironmentFile`, **nicht** im Repository.

## Warum Mailversand das Backup nicht fehlschlägt

SMTP-Fehler setzen nur `notification_email_status: failed` im Jobstatus. `code` und `status` des Backups bleiben unverändert.

## Jobstatus-Felder

- `notification_email_enabled`
- `notification_email_status` (`sent`, `failed`, `skipped_*`)
- `notification_email_sent`
- `notification_email_error`
- `notification_email_to_configured`
- `notification_email_recipient_masked` (z. B. `v***@example.com`)

## Implementierung

- `backend/core/notification_service.py`
- Aufruf aus `backend/tools/backup_runner.py` nach Erfolgs-`_update_status`
