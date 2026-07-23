# Windows 11 Instrumented Setup Runbook

1. `POST /api/rescue/win11-capture/prepare` → Run-ID.
2. Ensure SETUP_LOGS writable (TAG + write probe).
3. Start `collect-win11-live-capture.ps1` with Run-ID (periodic) **before** setup.exe.
4. Run Windows Setup from media; do not invent unsupported flags.
5. On hang/power-loss: stick still holds heartbeats/partial copies.
6. Finalize: count Panther/Rollback; status `evidence_collected` or `insufficient_evidence`.
7. Never mark success without artifacts.
