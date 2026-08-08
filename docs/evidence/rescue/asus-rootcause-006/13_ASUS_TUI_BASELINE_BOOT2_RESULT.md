# 13 ASUS TUI-Baseline Boot2 — 20260808_064943

**Campaign:** PI-RS-ASUS-ROOTCAUSE-006B  
**Classification input for Phase 3**  
**Hard expectations:** `PASS`

| Feld | Wert |
|------|------|
| Boot stamp | `20260808_064943` |
| Boot-ID | `a53ca88a-67ef-40bf-a3f7-c0ac0485d904` |
| Profile | ASUS-TUI-BASELINE |
| Payload | `1.10.5.0` |
| SquashFS | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` |
| Kernel | `Linux setuphelfer-rescue 6.1.0-52-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.180-1 (2026-08-03) x86_64 GNU/Linux` |
| BIOS | `G513QM.331` |
| Product | `ROG Strix G513QM_G513QM` |
| console_owner | `tui_owned` |
| Collector status | `ok` |
| Gate status | `blocked` |
| restore_allowed | `False` |

## Expectations

| Check | OK |
|-------|----|
| tui_console_owner | yes |
| gui_false | yes |
| startx_false | yes |
| chromium_false | yes |
| xorg_absent | yes |
| no_gui_processes | yes |
| failed_units_zero | yes |
| amdgpu_loaded | yes |
| edp_connected | yes |
| mt7921e_loaded | yes |
| r8169_loaded | yes |
| nvidia_not_loaded | yes |
| write_allowed_false | yes |
| collector_rc_ok | yes |

## MCE lines

```
[    7.410361] MCE: In-kernel MCE decoding enabled.
```

## MODE2 lines

```
[    8.431366] amdgpu 0000:06:00.0: amdgpu: MODE2 reset
```

## Gate reasons

```json
[
  "memory baseline reports immediate_issue_detected.",
  "cpu baseline reports immediate_issue_detected."
]
```

## Note

Boot2 verwendet den bereits physisch ausgeführten Run `20260808_064943` — Precheck `identical_test_conditions=true`, Software-Identität zu Boot1 bestätigt, **keine** Codeänderung vor diesem Run.
