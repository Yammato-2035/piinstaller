# Build mode decision

## Decision: **payload_repack**

| Criterion | Result |
|-----------|--------|
| Kernel changed | no |
| Initramfs changed | no |
| New packages | no |
| Inject path covers diagnostic + persistence modules | yes (`inject-gui-bvr-fixes-into-stick-squashfs.sh` syncs all `rescue_*.py`) |
| systemd unit + Wants | yes |

Not chosen: `controlled_live_build` (unnecessary).

Official paths:
- Repack: `scripts/rescue/inject-gui-bvr-fixes-into-stick-squashfs.sh`
- USB updater: `scripts/rescue-live/update-fat32-esp-live-payload.sh`
