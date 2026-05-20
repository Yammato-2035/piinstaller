# Backup-Benachrichtigungen (E-Mail)

## Erfolgs-Mail

- Auslöser: `backup.success` oder `backup.success_with_warnings` mit Verify Deep ok.
- Schalter: `SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS` (Standard: an).
- UI: Einstellungen → „Backup-Erfolg per E-Mail melden“.

## Fehler-Mail

- Auslöser: `backup.failed`, `backup.blocked_package_activity`, I/O-Fehler, Inhibit-Fehler u. a. Terminalfehler.
- Schalter: `SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE` (Standard: aus, nach Konfiguration an).
- UI: Einstellungen → „Bei Backup-Fehler E-Mail senden“.
- Betreff: `Setuphelfer — Backup fehlgeschlagen (<job_id>)`.

### Inhalt (keine Secrets)

- Job-ID, Status/Code, Diagnose, Abbruchgrund
- Zielpfad, Profil, Laufzeit, geschriebene Bytes
- finales Archiv ja/nein, Partial-Pfad, Partial gelöscht
- `tar_return_code`, `tar_warning_classification`
- Fehlerkern (gekürzt)
- Hinweis: Kein Restore ohne Verify Deep

### Runner-Kontext (systemd `setuphelfer-backup@.service`)

- Der Backup-Runner lädt **`load_effective_notification_config()`** aus `/etc/setuphelfer/notification.env` (wie die Settings-API), nicht nur Prozess-`os.environ`.
- Die Unit enthält `EnvironmentFile=-/etc/setuphelfer/notification.env` (zusätzlich zur Datei-Ladung im Code).
- Wenn die API `on_backup_failure=true` zeigt, der Runner aber `skipped_disabled` meldete: typisch fehlende Env-Datei im Runner — nach Deploy/Fix nicht mehr.

### Wann keine Mail

- `skipped_disabled`: E-Mail global aus
- `skipped_not_configured`: SMTP unvollständig
- `skipped_not_applicable`: Failure-Notify aus oder kein Fehlerstatus

SMTP-Fehler ändern den Backup-Status nicht (`notification_status=failed` im Job).

## Beispiel backup.failed (BR-001)

- `backup.failed` / `tar_failed` / `TAR_CRITICAL_WARNING`
- Live-Datei (z. B. Chrome-Cache) → kein finales Archiv, kein SHA256, kein Verify Deep
