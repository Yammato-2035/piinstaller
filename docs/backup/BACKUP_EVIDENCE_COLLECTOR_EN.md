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
