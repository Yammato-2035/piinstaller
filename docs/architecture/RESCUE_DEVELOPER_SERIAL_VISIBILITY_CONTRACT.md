# Rescue Developer QEMU — Serial Visibility Contract

**Scope:** `developer-qemu` live-build profile only. Release/standard profiles unchanged.

## Kernel / live boot append (SOLL)

```
boot=live components init=/lib/systemd/systemd
console=tty0
console=ttyS0,115200n8
loglevel=7
systemd.log_level=debug
systemd.show_status=true
ignore_loglevel
printk.devkmsg=on
setuphelfer_rescue=1
hostname=setuphelfer-rescue
username=user
… keyboard/locale/timezone …
```

**Must NOT include:** `quiet`, `splash`

## Boot paths

- live-build `--bootappend-live` → ISOLINUX + GRUB live entries (hybrid ISO)
- Regenerated via `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu` + `prepare-controlled-live-build-tree.sh` + controlled ISO build

## Serial markers (guest → ttyS0)

| Marker | When |
|--------|------|
| `SETUPHELFER_BOOT_MARKER_START` | Early systemd oneshot (`setuphelfer-serial-boot-markers.service`) |
| `SETUPHELFER_SYSTEMD_MARKER_START` | Autopilot start |
| `SETUPHELFER_AUTOPILOT_START` | Autopilot (includes `run_id=`) |
| `SETUPHELFER_DEVSERVER_AGENT_START` | Before agent Python block |
| `SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT` | Before agent send |
| `SETUPHELFER_DEVSERVER_AGENT_ERROR:*` | On agent send failure |

No secrets, no disk writes, lab URL `http://10.0.2.2:8001` allowed.

## Host QEMU wrapper (Fleet finish SOLL)

On finish, persist:

- `qemu.exit_code` (e.g. 124 on timeout)
- `qemu.acceleration` (`kvm` / `tcg`)
- `host.kvm_enabled`, `host.has_kvm`
- `serial.path`, `serial.exists`, `serial.size_bytes`
- findings: `serial_empty`, `classification_hint_serial_empty_boot_unknown` when size 0

## ISO rebuild

**Workspace tree / existing `binary.hybrid.iso` are stale until rebuild.**  
Next step: `REBUILD_DEVELOPER_RESCUE_ISO_WITH_SERIAL_VISIBILITY` (separate operator task).
