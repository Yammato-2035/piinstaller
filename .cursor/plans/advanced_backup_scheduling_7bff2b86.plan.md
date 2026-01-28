---
name: Advanced backup scheduling
overview: Add Cloud as a backup target, replace the schedule UX with multi-rule scheduling (per weekday/time/type/data-set), and make scheduled/manual backups optionally upload to WebDAV with verification and safe cleanup.
todos:
  - id: schema-migration
    content: Extend backup settings schema to schedules[] + datasets and migrate old schedule
    status: completed
  - id: systemd-multi-rule
    content: Generate one systemd timer+service per enabled rule
    status: completed
  - id: runner-per-rule
    content: Update runner to execute rule (full/inc/data/personal), upload with retries, verify, and cloud-only cleanup
    status: completed
  - id: cloud-target-manual
    content: Add Cloud as target in manual backup creation and implement upload/verify flow
    status: completed
  - id: ui-schedules
    content: Replace schedule UI with multi-rule editor; rename action button to “Einstellungen übernehmen”
    status: completed
  - id: ui-external-list
    content: "Enhance external backups list: refresh/filter by rule and show verification status"
    status: completed
  - id: version-bump
    content: Bump version to next MINOR (4-part scheme)
    status: completed
isProject: false
---

## Goals

- Add **Cloud** as a selectable target in **"Backup erstellen"**.
- Replace the current single schedule with **multiple schedule rules** (e.g. Mon 02:00 full, Tue–Sun 04:00 incremental, daily personal data; optionally incremental).
- Make the “Cloud” workflow **safe**: create locally, upload, **verify**, then (per your choice) delete local copy only after successful upload.
- Rename the settings-side action button to reflect what it does (**"Einstellungen übernehmen"**).

## Key decisions (based on your answers)

- **Cloud target behavior**: local file is deleted after successful upload (**cloud-only**).
- **Personal data scope**: presets apply to **all `/home/*` users**.
- **Scheduling implementation (safest + simplest to operate)**: keep using **systemd timers**, but generate **one timer+service per rule**, calling a single runner script with a rule id.

## Data model changes

- Extend `/etc/pi-installer/backup.json` from single `schedule` to:
- `schedules: [ { id, enabled, name, on_calendar, type, dataset, incremental, retention_keep_last, target } ]`
- `datasets`: named sets for `personal` presets and custom path lists.
- `cloud`: existing settings reused.
- `state`: per-rule metadata (last_full_epoch, last_run_epoch, last_uploaded_name, etc.).
- Provide a migration path: if old `schedule` exists, auto-create one default rule.

## Backend changes

- **Runner refactor** (generated at `/usr/local/bin/pi-installer-backup-run` from [backend/app.py](/home/gabrielglienke/Documents/PI-Installer/backend/app.py)):
- Accept CLI arg `--rule <id>`.
- Resolve backup plan from `/etc/pi-installer/backup.json`.
- Implement backup types:
- `full`: system full tar
- `incremental`: base = last full matching rule; if none → create full
- `data`: current data set (/home,/var/www,/opt) as today
- `personal`: tar of selected per-user folders under `/home/*` (e.g. Downloads, Documents, Pictures, Videos, Desktop) with optional incremental.
- Upload behavior:
- Create locally → upload via WebDAV (`curl -T`) with retry/backoff on transient failures.
- Verify remote existence (PROPFIND/HEAD) and size > 0.
- Only after verified: delete local file (cloud-only).
- If upload fails: keep local and report in stdout/stderr.
- Verification:
- Local: gzip/tar test (as already used elsewhere).
- Remote: PROPFIND for the uploaded filename.
- Retention:
- Apply per rule (keep_last) on local and/or remote depending on target.

- **systemd generation** in `_apply_backup_schedule`:
- Generate `pi-installer-backup-<ruleid>.service` + `.timer` per enabled rule.
- Service executes: `/usr/local/bin/pi-installer-backup-run --rule <ruleid>`
- Timer uses `OnCalendar=<rule.on_calendar>` (supports Mon/Tue.. patterns).
- Disable/remove timers for deleted/disabled rules.

- **API**:
- Replace `/api/backup/settings` schema to include schedules/datasets; keep backward compatibility.
- Expand cloud endpoints:
- Keep `GET /api/backup/cloud/list` but add optional `?rule_id=` and show remote retention/verification.
- Add `POST /api/backup/cloud/verify` (verify a specific remote filename).

## Frontend changes

- In [frontend/src/pages/BackupRestore.tsx](/home/gabrielglienke/Documents/PI-Installer/frontend/src/pages/BackupRestore.tsx):
- **Backup erstellen**: add new target card/button **Cloud**.
- When selected: require cloud settings enabled + tested, show warning that local will be deleted after verified upload.
- Trigger manual backup as "local create + upload" (new backend param or a follow-up call to upload).
- **Backup-Einstellungen**:
- Replace the current single schedule UI with a **Rules list**:
- Add/edit/remove rules
- For each rule: days-of-week picker + time, backup type (full/incremental/data/personal), incremental toggle (where applicable), retention keep_last, target (local/cloud/both)
- For `personal`: folder preset multi-select and scope `/home/*`
- Change button label **"Jetzt ausführen" → "Einstellungen übernehmen"** (this saves settings + regenerates timers). Provide a separate explicit **"Regel jetzt ausführen"** per rule if desired.
- External backups display:
- Reuse the existing external list, but allow filtering by rule/dataset and show verification status.

## Safety / UX

- Clear warnings for destructive actions:
- cloud-only deletes local files only after remote verification.
- Log and surface status:
- show last run time + last outcome per rule.
- Keep existing manual local backup workflow unchanged unless Cloud is selected.

## Files to touch

- Backend:
- [backend/app.py](/home/gabrielglienke/Documents/PI-Installer/backend/app.py) (settings schema, timer generation, runner script template, new endpoints)
- Frontend:
- [frontend/src/pages/BackupRestore.tsx](/home/gabrielglienke/Documents/PI-Installer/frontend/src/pages/BackupRestore.tsx) (Cloud target, new schedule UI, button rename)

## Versioning

- This is new functionality → bump to `MAJOR.MINOR.BUGFIX.HOTFIX` as **MINOR++** and reset bugfix/hotfix (e.g. `1.9.0.0`).