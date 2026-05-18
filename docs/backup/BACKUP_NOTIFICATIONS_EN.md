# Backup success: email notifications

## When is email sent?

Only after a completed backup job with:

- **`backup.success`**, or
- **`backup.success_with_warnings`** with **`backup_integrity_status: verified`** and successful runner **verify deep**

Not for `backup.failed`, `backup.warning_not_promoted`, missing archive, or failed verify.

## Why verify is required for warnings

BR-001 integrity requires a final archive, SHA256, and verify deep. Notifications must not imply success when that chain failed.

## Settings UI

Use **Settings → Email notifications** to set recipient, SMTP host, username, and a **Gmail app password**. The password is never returned by the API (`smtp_password_set` only). Use **Send test email** to verify SMTP without starting a backup.

For Gmail, an **app password** is usually required (Google account → Security), not your normal login password.

## Configuration (environment)

Environment variables (see `.env.example`). Store secrets in `.env` or systemd `EnvironmentFile` only — **never** commit credentials.

## Mail failures do not fail the backup

SMTP errors only set `notification_email_status: failed` on the job. Backup `code`/`status` stay success.

## Implementation

- `backend/core/notification_service.py`
- Invoked from `backend/tools/backup_runner.py` after success status update
