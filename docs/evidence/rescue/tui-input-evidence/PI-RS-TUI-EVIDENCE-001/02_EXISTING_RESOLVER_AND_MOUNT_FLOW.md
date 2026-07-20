# Existing resolver and mount flow

## Call chain (after fix)

```
setuphelfer-rescue-tui-input-diagnostic.service
→ /usr/local/sbin/setuphelfer-rescue-tui-input-diagnostic
→ core.rescue_tui_input_diagnostic.main / run_tui_input_diagnostic
→ resolve_evidence_root → resolve_runtime_evidence_root (/run/...)
→ runtime writers + finalize_run_dir(runtime)
→ finally: complete_diagnostic_persistence
→ wait_for_persistent_evidence_root (bounded)
→ resolve_setup_logs(allow_mount=True) via existing rescue_setup_logs_resolver
→ persist_runtime_evidence (.partial → verify → os.replace)
→ build_diagnostic_shutdown_decision
→ optional auto_shutdown only if shutdown_allowed
```

## Key modules

| Step | File | Function | Notes |
|------|------|----------|-------|
| Runtime root | `rescue_tui_input_diagnostic_persistence.py` | `resolve_runtime_evidence_root` | always `/run/...` or override |
| SETUP_LOGS | `rescue_setup_logs_resolver.py` | `resolve_setup_logs` | reused; mount only in finalizer |
| Wait | persistence | `wait_for_persistent_evidence_root` | timeout 60s / interval 2s |
| Migrate | persistence | `persist_runtime_evidence` | `.partial` + SHA verify |
| Finalize artifacts | `rescue_tui_input_diagnostic_evidence.py` | `finalize_run_dir` | manifest + SHA256SUMS |
| Import | `scripts/rescue/import-tui-input-diagnostic-runs.sh` | bash | skips `.partial` |
| Unit | systemd diagnostic unit | After/Wants setup-logs-resolver | soft Wants, no Requires |

`allow_mount=False` remains correct for diagnose **start**; finalizer uses safe mount.
