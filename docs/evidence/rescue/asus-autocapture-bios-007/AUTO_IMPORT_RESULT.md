# AUTO_IMPORT_RESULT

Dispatcher: `scripts/rescue/import-asus-lab-runs`

Default sources: import-queue, `asus-lab-runs/*/AUTO_IMPORT.READY`, `asus-win11/*` with finalize/ready.
Legacy `physical_runs/hw-discovery-*` only with `--include-legacy-hw` (not default).

Gates: Run-ID schema (or legacy hw-discovery), exact identity, redaction, idempotent `imported.marker`.
Quarantine: `docs/evidence/rescue/asus-lab-quarantine/`.
