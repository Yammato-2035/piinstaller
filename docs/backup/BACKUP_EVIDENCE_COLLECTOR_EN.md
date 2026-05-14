# Backup evidence collector

## Purpose

Collect diagnostics after a backup job finishes (success or failure) without mutating the job.

## Output locations

1. `/var/lib/setuphelfer/evidence/backup-jobs/<job_id>/`  
2. If not writable: `/tmp/setuphelfer-evidence-<job_id>/`

## Contents

Copies `status.json`, `job.json`, tar stderr log when present; `systemctl` status/show; `journalctl` (unit + kernel) and `dmesg` when permitted; SHA256 digests of `backup_runner.py` and `app.py` under `/opt/setuphelfer/backend/`. Missing privileges are recorded as `permission_denied` in `manifest.json`.

## Invocation

- Automatically when the runner reaches `_mark_terminal` with an active pipeline context.
- Manual: `python3 backend/tools/backup_evidence_collector.py --job-id <ID> …`

## API (UI / support)

- **`GET /api/backup/jobs/{job_id}/evidence`** — reads an existing `manifest.json` (does **not** start backup or restore). Always **HTTP 200** with contract field **`evidence`**: `evidence_status`, `evidence_dir`, `manifest_path`, `collected_sources`, `permission_denied_sources`, `errors`. If no manifest yet: `evidence_status: not_available` (not a 500).
- **`POST /api/backup/jobs/{job_id}/evidence`** — runs the collector again (still **no** backup/restore). Denied privileges appear in **`permission_denied_sources`**; hard issues in **`errors`**, still **HTTP 200** with structured body (no blanket 500 for `journalctl`/root).

The web UI (“Create / refresh evidence”, “Show manifest”) calls these endpoints; see i18n key `runningBackup.evidence.hintPaths` for filesystem paths.
