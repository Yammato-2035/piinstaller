# Rescue ISO Serial Boot Visibility — Fix Result

**Stand:** 2026-06-01 · **HEAD (Workspace):** nach Commit „Prepare rescue developer serial boot visibility“

## Umgesetzt (ohne ISO-Rebuild, ohne QEMU)

### 1. Prepare / live-build (`developer-qemu`)

`scripts/rescue-live/prepare-controlled-live-build-tree.sh`:

- `LIVE_BOOTAPPEND` für `developer-qemu`: `console=tty0`, `console=ttyS0,115200n8`, `loglevel=7`, `systemd.log_level=debug`, `systemd.show_status=true`, `ignore_loglevel`, `printk.devkmsg=on`
- **Entfernt:** `quiet`, `splash` (nur in diesem Profil)
- Standard-/Developer-Profil ohne `-qemu`: unverändert mit `quiet splash`

### 2. Profil `build/rescue/profiles/developer-qemu/`

- Neu: `setuphelfer-serial-boot-markers.sh` + `setuphelfer-serial-boot-markers.service` → `SETUPHELFER_BOOT_MARKER_START`
- Autopilot: `SETUPHELFER_SYSTEMD_MARKER_START`, `SETUPHELFER_AUTOPILOT_START`, `SETUPHELFER_DEVSERVER_AGENT_*`
- Hook 090: enable Serial-Marker + Autopilot

### 3. QEMU-Wrapper / Fleet-Finish

- `run-qemu-developer-iso-smoke.sh`: Finish exportiert `FLEET_SERIAL_PATH`, KVM/Acceleration, Findings bei leerem Serial
- `fleet-session-api.sh`: Finish-Payload mit `serial.path/exists/size_bytes`, `qemu.exit_code`, `qemu.acceleration`, `host.kvm_enabled`

### 4. Tests

- `scripts/tests/test_rescue_developer_serial_cmdline_v1.sh` — **OK**
- `backend/tests/test_rescue_developer_serial_visibility_v1.py` — **OK**
- `backend/tests/test_rescue_qemu_smoke_autopilot_profile_v1.py` — **OK**

## Nicht geändert

- **Kein** `lb build`, **keine** neue ISO.
- `build/rescue/live-build/setuphelfer-rescue-live/auto/config` im Tree bleibt bis zum nächsten Prepare+Build **stale** (`quiet splash`).

## current_iso_not_updated_until_rebuild

Die produktive/evidence-ISO `binary.hybrid.iso` (Lauf 081222) enthält weiterhin `quiet splash`. Erst nach:

```bash
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
# danach separater Operator-Auftrag:
# REBUILD_DEVELOPER_RESCUE_ISO_WITH_SERIAL_VISIBILITY
```

… gilt die Serial-Cmdline im bootfähigen Medium.

## Nächster Schritt

1. `REBUILD_DEVELOPER_RESCUE_ISO_WITH_SERIAL_VISIBILITY` (Operator, controlled build)
2. QEMU-Smoke-Retry mit Diagnose-Export + Serial-Log > 0 erwartet
