# Windows 11 Instrumented Setup Runbook

Critical path for ASUS Gabriel after PI-RS-ASUS-LAB-CONTROL-006.

## Preconditions

- Stick payload `1.10.3.1` with matching squashfs SHA256
- Volume `SETUP_LOGS` writable (`SETUP_LOGS.TAG` + write probe)
- Machine identity expected: G513QM / profile `ASUS_ROG_GABRIEL_LAB`
- BitLocker: read-only status only — no mutation

## Steps

1. `POST /api/rescue/win11-capture/prepare` (or generate) → `run_id=asus-win11-…`
2. Export `SETUPHELFER_WIN11_RUN_ID=<run_id>`
3. Start capture **before** setup:
   - `collect-win11-live-capture.ps1 -RunId <run_id>`
   - or `run-win11-setup-wrapper.cmd` (starts capture, then setup.exe)
4. Do **not** invent unsupported setup flags. `/noreboot` only if explicitly verified for that setup.exe.
5. On hang/reboot: stick should hold heartbeats under `SETUP_LOGS/asus-win11/<run_id>/heartbeats/`
6. Finalize: count Panther/Rollback; status `evidence_collected` or `insufficient_evidence`
7. Import **only** by Run-ID — never merge with older sessions (e.g. 095959Z)

## Forbidden

- Claiming freeze root cause from missing logs alone
- `unknown-norunid` on a controlled run
- BitLocker mutation
- BIOS 335 / Mint install in the same physical step as the first instrumented setup
