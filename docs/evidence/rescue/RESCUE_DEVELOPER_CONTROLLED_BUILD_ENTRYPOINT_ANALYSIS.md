# Rescue Developer Controlled Build — Entrypoint Analysis

**Date:** 2026-05-31  
**HEAD:** 54e9ce1  

## Build entrypoint (canonical)

| Field | Value |
|-------|-------|
| Script | `scripts/rescue-live/run-controlled-iso-build-with-logging.sh` |
| Confirm flag | `--operator-confirm-build` |
| Profile flag | `--profile developer` |
| Run-ID flag | `--run-id rescue_developer_iso_YYYYMMDD_HHMMSS` |
| Build command | `env PATH=build/rescue/tool-compat/bin:$PATH lb build noauto` |
| Build tree | `build/rescue/live-build/setuphelfer-rescue-live` |

## Preparation pipeline (developer)

| Step | Script |
|------|--------|
| 1. Temp runtime bundle | `scripts/rescue-live/create-temp-runtime-bundle.sh` |
| 2. Prepare tree (developer) | `SETUPHELFER_RESCUE_BUILD_PROFILE=developer ./scripts/rescue-live/prepare-controlled-live-build-tree.sh` |
| 3. Validate tree | `scripts/rescue-live/validate-controlled-live-build-tree.sh` |
| 4. Preflight | `scripts/rescue-live/preflight-developer-controlled-iso-build.sh <run-id>` |
| 5. Build | `run-controlled-iso-build-with-logging.sh --operator-confirm-build --profile developer --run-id <id>` |

## Developer profile materialization

When `SETUPHELFER_RESCUE_BUILD_PROFILE=developer`:

- Copies `build/rescue/profiles/developer/environment/setuphelfer-dev-agent.env` → chroot `/etc/setuphelfer/`
- Installs rescue-adapted `setuphelfer-dev-agent.service` (python3 + PYTHONPATH, local_lab)
- Enables agent in hook `010-enable-setuphelfer-services.hook.chroot`
- Writes marker `opt/setuphelfer-rescue/config/rescue-developer-profile.json`

## Output paths

| Artifact | Path |
|----------|------|
| ISO (on success) | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Build log | `build/rescue/logs/controlled-iso-build/latest.log` |
| Summary | `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json` |
| Developer result | `docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_result.json` |

## Safety gates

- Policy guard: root OR TTY+sudo OR `sudo -n` allowlist
- No USB/dd/mkfs in wrapper script
- Public profile guard before build
- `usb_write_allowed=false`, `dd_executed=false` in summary JSON

## Known risks (2026-05-31 run)

| Risk | Impact |
|------|--------|
| Agent environment without TTY/sudo | Build blocked exit **30** |
| Prior `binary/` owned by root | `./auto/clean` fails without sudo |
| Prior ISO artifacts in tree | Must archive/clean before rebuild |

## Operator command (manual terminal)

```bash
cd /home/volker/piinstaller
RUN_ID="rescue_developer_iso_$(date -u +%Y%m%d_%H%M%S)"
ARCHIVE="build/rescue/archive/prior-controlled-builds/${RUN_ID}"
mkdir -p "$ARCHIVE"
[ -f build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso ] && mv build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso "$ARCHIVE/"
sudo rm -rf build/rescue/live-build/setuphelfer-rescue-live/{binary,chroot,cache,local} || true
./scripts/rescue-live/create-temp-runtime-bundle.sh
SETUPHELFER_RESCUE_BUILD_PROFILE=developer ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/preflight-developer-controlled-iso-build.sh "$RUN_ID"
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile developer --run-id "$RUN_ID"
```
