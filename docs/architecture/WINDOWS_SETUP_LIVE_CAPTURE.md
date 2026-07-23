# Windows Setup Live Capture

Evidence during Windows Setup must land on the rescue stick **before** hangs, not only via post-mortem NTFS scans.

## Run identity

```text
run_id = asus-win11-<UTC timestamp>-<8 hex>
```

Forbidden: `unknown-norunid`, `norunid`, empty. Same run_id on collector, heartbeats, wrapper, SetupDiag, import, final report.

## Destination

Primary: volume label / `SETUP_LOGS.TAG` (never drive letter alone).

```text
SETUP_LOGS/asus-win11/<run_id>/{collector,heartbeats,winpe,panther,rollback,setupdiag,disk-layout,firmware,screenshots,result}
```

Prepare requires inventoy → label → free space → run folder → write/flush probe → `setup_capture_ready`.

## Sources (best effort)

```text
X:\Windows\Panther
X:\$WINDOWS.~BT\Sources\Panther
X:\$WINDOWS.~BT\Sources\Rollback
C:\$WINDOWS.~BT\Sources\Panther
C:\$WINDOWS.~BT\Sources\Rollback
C:\Windows\Panther
```

Missing paths are normal and logged; they must not crash the collector.

## Heartbeat

Periodic JSON (≥ schema in ticket) with `collector_alive`, copy counters, `last_copy_error`, `setup_logs_volume_present`.

## Scripts

- `SETUPHELFER_WIN_DIAG/collect-win11-live-capture.ps1` — periodic copy + heartbeat
- `SETUPHELFER_WIN_DIAG/run-win11-setup-wrapper.cmd` — start capture, invoke setup.exe, final flush
- Backend: `rescue_win11_live_capture.py`

## Finalize statuses

| Condition | Status |
|-----------|--------|
| Invalid run_id | `blocked` |
| Panther or Rollback files > 0 | `evidence_collected` |
| Heartbeats but no files | `insufficient_evidence` |
| No heartbeats | `collector_missing` |

Never claim a definitive freeze root cause from missing logs alone. Never treat SetupDiag success without sources.

## APIs

- `POST /api/rescue/win11-capture/prepare`
- `POST /api/rescue/win11-capture/finalize`
- `GET /api/rescue/win11-capture/{run_id}`
