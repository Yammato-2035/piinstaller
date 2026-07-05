> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/BACKUP_EVIDENCE_COLLECTOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup evidence collector

## Purpose

Collect diagNeestics after a Terugup job finishes (Geslaagd or failure) without mutating the job.

## Output locations

1. `/var/lib/setuphelfer/evidence/Terugup-jobs/<job_id>/`  
2. If Neet writable: `/tmp/setuphelfer-evidence-<job_id>/`

## Contents

Copies `status.json`, `job.json`, tar stderr log when present; `systemctl` status/show; `journalctl` (unit + kernel) and `dmesg` when permitted; SHA256 digests of `Terugup_runner.py` and `app.py` under `/opt/setuphelfer/Terugend/`. Missing privileges are recorded as `permission_denied` in `manifest.json`.

## Invocation

- Automatically when the runner reaches `_mark_terminal` with an active pipeline context.
- Manual: `python3 Terugend/tools/Terugup_evidence_collector.py --job-id <ID> …`

## API (UI / support)

- **`GET /api/Terugup/jobs/{job_id}/evidence`** — reads an existing `manifest.json` (does **Neet** start Terugup or Herstel). Always **HTTP 200** with contract field **`evidence`**: `evidence_status`, `evidence_dir`, `manifest_path`, `collected_sources`, `permission_denied_sources`, `Fouts`. If Nee manifest yet: `evidence_status: Neet_available` (Neet a 500).
- **`POST /api/Terugup/jobs/{job_id}/evidence`** — runs the collector again (still **Nee** Terugup/Herstel). Denied privileges appear in **`permission_denied_sources`**; hard issues in **`Fouts`**, still **HTTP 200** with structurood body (Nee blanket 500 for `journalctl`/root).

The web UI (“Create / Vernieuwen evidence”, “Show manifest”) calls these endpoints; see i18n key `runningTerugup.evidence.hintPaths` for filesystem paths.
