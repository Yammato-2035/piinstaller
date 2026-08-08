# Boot3 Preparation — ASUS-TUI-BASELINE-HIGHINFO

## Carrier gate

**`carrier_1_10_6_0_verified`**

## Run plan

| Item | Value |
|------|-------|
| Profile | `ASUS-TUI-BASELINE-HIGHINFO` (GRUB default=0) |
| Payload | `1.10.6.0` |
| Chromium | disabled until Xorg ready |
| NVMe writes | **forbidden** |
| Stages | TUI → inventory → CPU/RAM → storage → gaps → network → telemetry → Xorg probe → diagnostics → install readiness → evidence flush |

## Operator actions

1. Boot ASUS from Setuphelfer USB (UEFI).
2. Confirm TUI visible / usable.
3. Let highinfo stages complete (do not force GUI).
4. After boot: return stick or copy `SETUP_LOGS` evidence to host for import.

## Suggested Run-ID

`asus-highinfo-boot3-20260808` (or stick-generated boot session id)
