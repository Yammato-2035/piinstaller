# 04 Boot-1 TUI-Baseline Evidence

**Status:** `boot1_tui_baseline_pass_with_notes`  
**Boot:** `20260808_064943` / boot_id `a53ca88a-67ef-40bf-a3f7-c0ac0485d904`  
**Profil:** ASUS-TUI-BASELINE  
**Payload auf Stick:** `1.10.5.0`  
**SquashFS:** `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51`  
**GRUB:** `fb7b8d5b4937e5a666ae544e81ae07d01cd8c2218831b421242e2b8a2c91e3ea`

## Hard Checks

| Check | OK |
|------|----|
| profile_asus_tui_baseline | yes |
| console_owner_tui_owned | yes |
| gui_started_false | yes |
| startx_started_false | yes |
| chromium_started_false | yes |
| nvme_writes_false | yes |
| hardware_baseline_ok | yes |
| boot_diagnostics_rc_0 | yes |
| no_xorg_log | yes |
| no_failed_systemd_units | yes |

## Yellow Notes

- runtime_diagnostics_rc=1 (non-zero; does not alone fail TUI baseline gate)
- boot_stage_state.boot_profile still reports ASUS-00 while cmdline is ASUS-TUI-BASELINE (sentinel drift)
- boot-progress.json message still says GUI übernehmen during TUI baseline
- media-check spot_checks_ok=false (path spot checks); squashfs_hash_ok=true
- Stick payload is 1.10.5.0 (c57c6fb8…), not the 1.10.3.0 (4629ca61…) verified in 03_CARRIER_UPDATE_VERIFY — later update outside this worktree HEAD

## Prior TUI captures (same campaign)

| Stamp | Payload | Notes |
|------|---------|-------|
| 20260807_213327 | 1.10.4.0 | console tui_owned; hardware_baseline failed |
| 20260807_221550 | 1.10.5.0 | autocapture green-looking |
| 20260808_064943 | 1.10.5.0 | this analysis |

## Repro / Xorg gate

- `repro_status`: `two_green_tui_boots_on_1.10.5.0_observed`
- `xorg_forensic_allowed`: **False**
- Next: Either confirm prior 20260807_221550 counts as Boot1 and this morning as Boot2, then ACK for XORG-FORENSIC; or run one more intentional ASUS-TUI-BASELINE boot for clean Boot2 labeling.

## Fake-Green

Kein Claim `asus_tui_baseline_stable` / `gui_ready` ohne zweite bestätigte Baseline auf demselben Payload (oder explizite Operator-Anrechnung von 221550).
