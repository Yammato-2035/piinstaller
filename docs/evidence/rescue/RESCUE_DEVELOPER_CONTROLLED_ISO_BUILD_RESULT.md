# Rescue Developer Controlled ISO Build — Final Result

**Date:** 2026-05-31  
**HEAD Start:** 8455e3c
**Branch:** main  
**Version:** 1.7.3.0  
**Run-ID:** `rescue_developer_iso_20260531_103047`

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** |
| Backend-Version-Gate | **OK** |
| `/api/version` | 1.7.3.0 |
| Clean Runtime | **yes** |
| Dev-Server | enabled, local_lab, storage_ok |

## Build finalization

| Field | Value |
|-------|-------|
| Permission clean | **OK** (operator sudo clean completed) |
| Permission fix commit | `8455e3c` |
| LB_EXIT | **0** |
| Summary | `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json` |
| Build status (summary) | **success** |
| Execution mode | manual_operator_terminal |
| Build duration | ~3m36s (12:30:49–12:34:25) |

## ISO artifact

| Field | Value |
|-------|-------|
| ISO gefunden | **yes** |
| ISO-Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 509607936 bytes (~486 MiB) |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| SHA256-Datei | `docs/evidence/runtime-results/rescue/rescue_developer_iso_latest.sha256` |
| Prior archived ISO | unterschiedliche SHA256 (`1eccf9c0…`) — **neues Artefakt** |

## Build log

`build/rescue/logs/controlled-iso-build/latest.log` — endet mit `LB_EXIT=0`, `lb_binary_iso` erfolgreich (248826 extents, 485 MB).

## Static inspection (no mount)

| Tool | Available |
|------|-----------|
| xorriso | **yes** |
| isoinfo | **yes** |

| ISO check | Result |
|-----------|--------|
| Volume ID | `SETUPHELFER_RESCUE` |
| Application ID | Setuphelfer Rescue Live |
| Boot | El Torito + isohybrid |
| `/live` | present |

Agent-Dateien liegen im `filesystem.squashfs` (nicht als Top-Level-ISO-Pfade). Nachweis über gebautes **chroot**:

| Path | Present |
|------|---------|
| `chroot/etc/setuphelfer/setuphelfer-dev-agent.env` | **yes** — local_lab, AUTO_UPLOAD=true |
| `chroot/etc/systemd/system/setuphelfer-dev-agent.service` | **yes** |
| Hook `010-enable-setuphelfer-services.hook.chroot` | **systemctl enable setuphelfer-dev-agent.service** |

## Developer Agent proof

| Check | Result |
|-------|--------|
| ENABLED | true |
| MODE | local_lab |
| AUTO_UPLOAD | true |
| SERVER_URL | http://127.0.0.1:8000 |
| SSH | false |
| Write actions | false |

## Public guard

| Check | Result |
|-------|--------|
| `check-dev-agent-rescue-profile-guard.sh` | exit **0** |
| Public profile | enabled=false, auto_upload=false, mode=public_rescue |
| Token | absent |
| Public URL | absent |

## Dry-build guard (post-controlled build)

Manifest: `docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest_post_controlled_build.json`

- Status: **review_required** (prior ISO artifacts in tree: 34)
- Public/Agent/Safety: **OK** (keine errors)

## Forbidden action scan

Aktuelles Result: `usb_write_started=false`, `dd_executed=false`, `boot_test_executed=false`, `target_device=null`.

Keine verbotenen Treffer im aktuellen Result/Summary.

## QEMU boot plan

| Field | Value |
|-------|--------|
| Runbook DE | `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_DE.md` |
| Runbook EN | `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_EN.md` |
| QEMU ausgeführt | **false** |
| USB ausgeführt | **false** |

## Safety

USB, dd, Boot, Backup, Restore, apt, mount: **not executed**

## Entscheidung

| Question | Answer |
|----------|--------|
| Controlled Developer ISO build | **SUCCESS** |
| ISO + SHA256 + Guards | **YES** |
| QEMU Boot | **pending** (Plan erstellt) |

**Next prompt:** **RESCUE DEVELOPER ISO QEMU BOOT SMOKE TEST**

## References

- `docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_result.json`
- `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_BUILD_PERMISSION_ANALYSIS.md`
- `docs/architecture/RESCUE_CONTROLLED_ISO_BUILD_PERMISSION_POLICY.md`
- `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_DE.md`
