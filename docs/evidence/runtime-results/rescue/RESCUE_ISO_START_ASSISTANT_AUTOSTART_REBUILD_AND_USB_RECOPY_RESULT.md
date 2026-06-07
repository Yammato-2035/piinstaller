# RESCUE ISO Start Assistant Autostart — Rebuild & USB Recopy Result

**Prompt:** `RESCUE_ISO_START_ASSISTANT_AUTOSTART_REBUILD_AND_USB_RECOPY_OPERATOR_RUN`  
**Run:** 2026-06-07T16:18:00+02:00  
**Workspace HEAD:** `9cc6c9a`  
**Version:** `1.7.9.0`  
**Outcome:** **BLOCKED** — ISO rebuild and USB recopy not completed in agent session

## Phase 0 — Sicherheitsgate

| Check | Result |
|-------|--------|
| Branch | `main` |
| HEAD | `9cc6c9a` |
| VERSION | `1.7.9.0` |
| `check_version_consistency.py` (workspace) | OK |
| `check-backend-version-gate.sh` | **Drift** — workspace `1.7.9.0`, API `1.7.8.4` (Exit 14) |
| Runtime drift blocks ISO build? | **No** — documented only |

### Zielgerät `lsblk`

| Device | Status |
|--------|--------|
| `/dev/sdb` | **NOT PRESENT** — `lsblk: kein blockorientiertes Gerät` |
| `/dev/sda` | HGST Backup — **not touched** |
| `/dev/nvme0n1`, `/dev/nvme1n1` | Present — **not touched** |

**Expected Ultra Line stick (Serial `24111412110212`) not connected during this run.**

Cached FAT UUID from prior staging: `1146-3CA1` (not re-read from stick — `/dev/sdb1` absent).

## Phase 1 — Clean ISO Rebuild

| Step | Result |
|------|--------|
| `clean-controlled-live-build-tree.sh --operator-confirm-clean` | **BLOCKED** — `sudo: Passwort notwendig` |
| `prepare-controlled-live-build-tree.sh` | **OK** — tree refreshed, profile=standard |
| `validate-controlled-live-build-tree.sh` | **FAIL Exit 11** — stale chroot forbidden firmware path (clean not run) |
| `run-controlled-iso-build-with-logging.sh --operator-confirm-build` | **BLOCKED Exit 30** — `blocked_requires_operator_sudo_policy` |

**Existing ISO on disk (unchanged, pre-1.7.9.0 squashfs):**

| Field | Value |
|-------|-------|
| Path | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Size | `683671552` bytes |
| SHA256 | `c70cdcfa329aae9b32909d4cada84dcb0d5b4433a298e7dc1a9b6b2b66631428` |
| LB_EXIT | 30 (no build executed) |

UEFI validator not re-run — ISO not rebuilt.

## Phase 2 — Build-tree vs SquashFS

### includes.chroot (after prepare) — **PASS**

All required scripts, packages, and systemd autostart fields present:

- `ConditionKernelCommandLine=setuphelfer_start_assistant=1`
- `TTYPath=/dev/tty1`, `StandardInput=tty`, `StandardOutput=tty`, `Environment=TERM=linux`
- `Conflicts=getty@tty1.service`
- `getty@tty1.service.d/setuphelfer-rescue.conf` with `!setuphelfer_start_assistant=1`
- `multi-user.target.wants/setuphelfer-rescue-start-assistant.service` symlink

### SquashFS inside existing ISO — **FAIL (stale)**

Extracted `live/filesystem.squashfs` from current ISO:

- **Missing** `getty@tty1.service.d/setuphelfer-rescue.conf`
- **Old** `setuphelfer-rescue-start-assistant.service`: `StandardOutput=journal`, no `ConditionKernelCommandLine`, no getty conflict handling

**STOP:** No USB handoff — ISO must be rebuilt with sudo before MSI test.

## Phase 3–6 — Not executed

| Phase | Reason |
|-------|--------|
| FAT32-ESP staging rebuild | Blocked on stale ISO / no rebuild |
| GRUB UUID patch from `/dev/sdb1` | `/dev/sdb` absent |
| USB rsync recopy | `/dev/sdb` absent, sudo mount unavailable |
| `verify-fat32-esp-rescue-usb.sh` | Not run — `VERIFY_RC=N/A` |

## Gate fields (this run)

| Field | Value |
|-------|-------|
| `iso_rebuilt_for_start_assistant_autostart` | **false** |
| `build_tree_prepared_for_1_7_9_0` | **true** |
| `fat32_esp_usb_verified` | **false** (not re-verified) |
| `target_laptop_booted_from_stick` | true (prior MSI run) |
| `target_boot_stage` | live_console |
| `target_network_telemetry_validated` | true |
| `last_ack_id` | rti-e5aa1b9979b346f8 |
| `start_assistant_autostart_validated` | **false** |
| `windows_inspect_executable` | false |

## Operator unblock (interactive terminal required)

```bash
cd /home/volker/piinstaller
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_START_ASSISTANT_AUTOSTART_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
# After LB_EXIT=0: validate ISO, rebuild staging, connect /dev/sdb, patch UUID, rsync recopy, verify
```

## MSI test freigegeben?

**Nein** — Stick enthält noch SquashFS ohne 1.7.9.0 Autostart-Fix.

## Next Prompt

`RESCUE_START_ASSISTANT_AUTOSTART_REBUILD_FAILURE_TRIAGE`
