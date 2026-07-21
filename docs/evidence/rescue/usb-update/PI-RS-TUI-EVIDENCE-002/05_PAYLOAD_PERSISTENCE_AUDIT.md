# Payload persistence audit

Extracted staging squashfs to `/tmp/tui-evidence-002-squashfs-audit`.

Verified present:
- `rescue_tui_input_diagnostic_persistence.py`
- `RUNTIME_EVIDENCE_BASE = /run/setuphelfer/tui-input-diagnostics`
- `wait_for_persistent_evidence_root`
- `persist_runtime_evidence` with `.<RUN_ID>.partial`
- `shutdown_allowed` / `build_diagnostic_shutdown_decision`
- systemd unit: `TTYPath=/dev/tty2`, `ConditionKernelCommandLine=setuphelfer_tui_input_diag=1`
- Version carriers inside squash: `1.10.0.60`

Forbidden static path note: `/media/volker/` appears only as **rejection** string in persistence module (not as write target). Other `/dev/sda` hits are pre-existing safety/forbid lists, not hard-coded write targets for this diagnostic path.
