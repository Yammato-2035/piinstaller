# E-Mail-Benachrichtigungen (Runtime) – Backend, `notification.env`, systemd

Kurzfassung für Betrieb und Forensik (keine Secrets, keine Passwörter in Logs).

## `notification.env`

- Pfad typisch: `/etc/setuphelfer/notification.env` (siehe API-Feld `env_path`).
- Enthält SMTP-Zugangsdaten — **nicht** in Git, **nicht** in API-Responses (`smtp_password_set` statt Klartext).
- Empfohlene Rechte (Operator): Verzeichnis `root:setuphelfer` **0770**, Datei **0660** (kein Weltlesen, kein `chmod 777`).

## Backend (`setuphelfer-backend.service`)

- **`NoNewPrivileges=true`:** Das Backend darf **kein** `sudo` ausführen. Schreiben nur direkt, wenn Unix-Rechte und ggf. systemd **`ReadWritePaths=/etc/setuphelfer`** passen.
- **Kein API-Request** (weder GET/POST Einstellungen noch `/api/system/status`) soll den Uvicorn-Prozess beenden. Fehler = strukturierte JSON-Antwort (`status: error`, `diagnosis_id`, …), **ohne** Passwort im `message`.
- **SMTP-Test:** nur über den Test-Endpunkt (`/api/settings/notifications/email/test`), nicht implizit beim Speichern.

## Häufige Fehlinterpretation „Backend abgestürzt“

- Bei **`--workers 1`** blockiert **lange synchron laufende** Arbeit im async-Handler alle parallelen HTTP-Anfragen (Symptom: Timeout / UI „Backend weg“), obwohl `systemctl` weiter **active** meldet.
- Ursache war u. a. `/api/system/status` mit teuren `apt`-Aufrufen im gleichen Thread wie der Event-Loop — siehe Evidence `docs/evidence/runtime-results/notification_settings_backend_crash_repair_2026-05-19.json` und Fix in `app.py` (`asyncio.to_thread`, vereinfachte Update-Kategorisierung).

## SMTP-/TLS-Fehler

- Werden als **Betriebsfehler** klassifiziert (`last_test_status`, `last_test_error_class`), nicht als Prozessfehler.

## Journal

- Vollständige Tracebacks: `sudo journalctl -u setuphelfer-backend.service -n 300 --no-pager`
