# Backup notifications (email)

## Success mail

- Trigger: `backup.success` or `backup.success_with_warnings` with Verify Deep ok.
- Switch: `SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS` (default: on).
- UI: Settings → notify on backup success.

## Failure mail

- Trigger: `backup.failed`, `backup.blocked_package_activity`, I/O errors, inhibit failures, etc.
- Switch: `SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE` (default: off until enabled).
- UI: Settings → send email on backup failure.
- Subject: `Setuphelfer — Backup fehlgeschlagen (<job_id>)`.

### Body (no secrets)

- Job ID, status/code, diagnosis, abort reason
- Target path, profile, runtime, bytes written
- final archive yes/no, partial path, partial deleted
- `tar_return_code`, `tar_warning_classification`
- Short error excerpt
- Note: no restore without Verify Deep

### When no mail is sent

- `skipped_disabled`, `skipped_not_configured`, `skipped_not_applicable`

SMTP errors do not change backup outcome (`notification_status=failed` on the job).
