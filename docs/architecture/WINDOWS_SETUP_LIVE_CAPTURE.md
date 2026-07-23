# Windows Setup Live Capture

Primary evidence during setup on `SETUP_LOGS` (label/TAG), not post-hang only.

- Run-ID: `asus-win11-<UTC>-<8hex>` — `unknown-norunid` forbidden for controlled runs.
- Layout under `SETUP_LOGS/asus-win11/<run_id>/` with heartbeats, panther, rollback, result.
- WinPE: `SETUPHELFER_WIN_DIAG/collect-win11-live-capture.ps1` (+ CMD wrapper).
- Finalize without files → `insufficient_evidence` (not success); with files → `evidence_collected`.
- No claim of freeze root cause from missing logs alone.
