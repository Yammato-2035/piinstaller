# PI-RS-ASUS-HIGHINFO-PHYSICAL-009 — Boot3 Baseline Freeze

## Workspace (Phase 0)

| Field | Value |
|-------|-------|
| Workspace | `/home/volker/piinstaller-asus-emergency-linux-telemetry-003` |
| Branch | `pi-rs-asus-autonomous-diag-install-007` |
| HEAD | `b6c6fd0b` |
| Origin | `https://github.com/Yammato-2035/piinstaller.git` |
| Erwarteter Ausgangs-HEAD `b6c6fd0b` enthalten | **ja** (ist HEAD) |

## Boot3 identity

| Field | Value |
|-------|-------|
| Boot stamp | `20260808_103635` |
| Kernel boot_id | `9abd33f8-aacd-4012-aa66-bfb52a8e16d3` |
| Payload | `1.10.6.0` |
| Profile (cmdline) | `ASUS-TUI-BASELINE-HIGHINFO` (`setuphelfer_highinfo=1`, `setuphelfer_xorg_probe=1`) |
| Product | ROG Strix G513QM |

## Proven on Boot3

| Area | Result | Classification |
|------|--------|----------------|
| TUI | stable | `current_boot` |
| console_owner | `tui_owned` | `current_boot` |
| failed systemd units | 0 | `current_boot` |
| AMD amdgpu + eDP connected | yes | `current_boot` |
| NVIDIA blacklist | intentional | `current_boot` |
| RAM | no_immediate_issue_detected | `current_boot` |
| nvme0n1 | Windows candidate | `current_boot` |
| nvme1n1 | empty / Linux target candidate | `current_boot` |
| NVME_WRITE_ALLOWED | **false** | hard rule |

## Not proven on Boot3

| Area | Result |
|------|--------|
| startx invoked | not proven |
| Xorg log (this boot) | missing (`/var/log/Xorg.0.log` absent; no mirrored forensic) |
| IONOS telemetry ACK / correlation_id | not proven |
| SMART complete | incomplete |
| Install image SHA256 | unverified |

## Evidence origin classification

| Artifact | Origin | usable_for_boot3 |
|----------|--------|------------------|
| `tui-baseline-autocapture-20260808_103635.json` | `current_boot` | true |
| `baseline-quick-20260808_103635.json` | `current_boot` | true |
| `diagnostics/20260808_103636_boot/*` | `current_boot` | true |
| `gui-fallback.json` (mtime 2026-08-07) | **`stale_previous_boot`** | **false** |
| prior autocapture `20260807_*` / `20260808_064943` | `stale_previous_boot` | false |

## Root cause (frozen until Boot4 proof)

```text
primary_failure_area=startx_not_invoked_or_evidence_not_persisted
confidence=0.88
```

Not rewritten retrospectively. Boot4 must supply boot-scoped Xorg evidence.

## Mirror fix status (repo vs stick)

| Item | Status |
|------|--------|
| Repo HEAD includes SETUP_LOGS mirror in `setuphelfer-rescue-highinfo-boot.sh` | yes (`b6c6fd0b`+) |
| Stick booted for Boot3 | **1.10.6.0 without post-Boot3 mirror enhancements** |
| Next payload | must carry structured `xorg_probe_evidence.json` + mirror |

## Hard stops for 009

- No NVMe write
- No installer
- Max terminal status: `ready_for_install_authorization` with `NVME_WRITE_ALLOWED=false`
