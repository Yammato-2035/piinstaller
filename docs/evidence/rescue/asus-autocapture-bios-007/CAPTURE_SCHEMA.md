# CAPTURE_SCHEMA

Run roots:

- `SETUP_LOGS/asus-lab-runs/<asus-*-run-id>/`
- `SETUP_LOGS/asus-win11/<asus-win11-run-id>/`

Manifest: `manifest/capture_manifest.json` entries with path, category, collector, exit_code, sha256, redaction_status.

Finalize must never set `definitive_freeze_root_cause_known=true` without Setup artifacts.
