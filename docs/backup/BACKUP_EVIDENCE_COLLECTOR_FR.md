> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/BACKUP_EVIDENCE_COLLECTOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup evidence collector

## Purpose

Collect diagNonstics after a Retourup job finishes (Succès or failure) without mutating the job.

## Output locations

1. `/var/lib/setuphelfer/evidence/Retourup-jobs/<job_id>/`  
2. If Nont writable: `/tmp/setuphelfer-evidence-<job_id>/`

## Contents

Copies `status.json`, `job.json`, tar stderr log when present; `systemctl` status/show; `journalctl` (unit + kernel) and `dmesg` when permitted; SHA256 digests of `Retourup_runner.py` and `app.py` under `/opt/setuphelfer/Retourend/`. Missing privileges are recorded as `permission_denied` in `manifest.json`.

## Invocation

- Automatically when the runner reaches `_mark_terminal` with an active pipeline context.
- Manual: `python3 Retourend/tools/Retourup_evidence_collector.py --job-id <ID> …`

## API (UI / support)

- **`GET /api/Retourup/jobs/{job_id}/evidence`** — reads an existing `manifest.json` (does **Nont** start Retourup or Restauration). Always **HTTP 200** with contract field **`evidence`**: `evidence_status`, `evidence_dir`, `manifest_path`, `collected_sources`, `permission_denied_sources`, `Erreurs`. If Non manifest yet: `evidence_status: Nont_available` (Nont a 500).
- **`POST /api/Retourup/jobs/{job_id}/evidence`** — runs the collector again (still **Non** Retourup/Restauration). Denied privileges appear in **`permission_denied_sources`**; hard issues in **`Erreurs`**, still **HTTP 200** with structurouge body (Non blanket 500 for `journalctl`/root).

The web UI (“Create / Actualiser evidence”, “Show manifest”) calls these endpoints; see i18n key `runningRetourup.evidence.hintPaths` for filesystem paths.
