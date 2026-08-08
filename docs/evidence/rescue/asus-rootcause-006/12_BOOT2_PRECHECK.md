# 12 Boot2 Precheck — PI-RS-ASUS-ROOTCAUSE-006B

**Status:** `identical_test_conditions = true`  
**Campaign:** PI-RS-ASUS-ROOTCAUSE-006B  
**Timestamp UTC:** 2026-08-08T07:39:26Z

## Boot1 Reference (`20260807_221550`)

| Feld | Wert |
|------|------|
| Payload | `1.10.5.0` |
| SquashFS | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` |
| Profile flags | `setuphelfer_rescue=1 setuphelfer_start_assistant=1 setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 setuphelfer_telemetry_opt_in=1 setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_tui_baseline=1 setuphelfer_gui_watchdog=0 pci=noaer modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm,nouveau setuphelfer_asus_profile=ASUS-TUI-BASELINE setuphelfer_auto_hw_baseline=1` |

## Carrier jetzt

| Feld | Wert |
|------|------|
| Device | `/dev/sda` |
| Fingerprint | `ce2e34b7f5ea4e41` |
| Serial | `24111412110212` |
| Payload | `1.10.5.0` |
| SquashFS | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` |
| GRUB SHA256 | `fb7b8d5b4937e5a666ae544e81ae07d01cd8c2218831b421242e2b8a2c91e3ea` |
| EFI GRUB SHA256 | `fb7b8d5b4937e5a666ae544e81ae07d01cd8c2218831b421242e2b8a2c91e3ea` |
| GRUB default | `0` |

## Checks

| Check | OK |
|-------|----|
| target_fingerprint_ok | yes |
| payload_1_10_5_0 | yes |
| squashfs_prefix_c57c6fb8 | yes |
| squashfs_matches_boot1 | yes |
| grub_has_asus_tui_baseline | yes |
| grub_default_0 | yes |
| boot1_profile_flags_present_in_grub | yes |

## ESP-Dateien mit mtime nach Boot1 (Kernpfade)

Count: **0**

- (keine)

## Kandidat bereits auf Stick: `20260808_064943`

| Feld | Wert |
|------|------|
| Payload | `1.10.5.0` |
| SquashFS | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` |
| cmdline flags == Boot1 | `True` |
| qualifies software identity | `True` |

## Regel

- `identical_test_conditions` = **true**
- Code-/Heuristikänderungen vor Boot 2: **verboten** (nicht ausgeführt)
- Boot2-Status: `candidate_already_present_may_use_as_boot2`

Wenn `identical_test_conditions=false`: Boot 2 **nicht** als Reproduzierbarkeitstest verwenden.
