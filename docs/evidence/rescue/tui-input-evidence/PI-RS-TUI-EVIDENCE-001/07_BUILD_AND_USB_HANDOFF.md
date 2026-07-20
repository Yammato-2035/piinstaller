# Build and USB handoff

```
Quellcommit: 3d494424fafecbfcdf2e2c4586b6b01ae7844ddf
Zielversion: 1.10.0.60
notwendiger Buildmodus: payload_repack (isolierter Worktree wie AUTO-002)
geänderte Payload-Dateien:
  - backend/core/rescue_tui_input_diagnostic*.py (+ persistence)
  - scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-input-diagnostic.service
  - config/rescue_payload_version.json
  - import script is host-side (optional on stick)
neue/angepasste Tests:
  - test_rescue_tui_input_evidence_persistence_v1.py
  - version asserts in test_rescue_tui_input_diagnostic_v1.py
erwarteter SquashFS-Pfad: (nach Build) artifacts/.../filesystem.squashfs
erwartete Versionsträger: rescue_payload_version.json / VERSION / runtime carriers = 1.10.0.60
USB-Updater: scripts/rescue-live/update-fat32-esp-live-payload.sh
Post-Write-Prüfungen: SquashFS + GRUB hashes; GRUB diag entry; payload version 1.10.0.60
Rollback: previous payload 1.10.0.59 stick image / prior squashfs
nächster MSI-Test: PI-RS-TUI-AUTO-003 retry after USB update — verify SETUP_LOGS/tui-input-diagnostics/<RUN_ID>/
```

STOP before build/USB in this task.
