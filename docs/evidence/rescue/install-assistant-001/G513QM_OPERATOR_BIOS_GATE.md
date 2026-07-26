# Operator Gate — Gabriel G513QM before next install

**Status:** pending operator confirmation (fill checkboxes on the machine).

Do **not** start another Mint install boot until all gates are YES.

## Checklist

| Gate | Required | Operator result | Notes |
|------|----------|-----------------|-------|
| BIOS version | **G513QM.335** (or newer official) | [ ] YES / [ ] NO — was: _______ | Update from Windows / ASUS support; 331 known on site earlier |
| Secure Boot | **Off** | [ ] YES / [ ] NO | |
| Fast Boot | **Off** | [ ] YES / [ ] NO | |
| Armoury Crate dGPU | **Auto** (not iGPU-only) | [ ] YES / [ ] NO | iGPU-only hides NVIDIA from Linux |
| Stick | Intenso SETUPHELFER + SETUP_LOGS with `mint-live` + `rog-pack/g513qm` | [ ] YES / [ ] NO | |
| GRUB default | Rescue-Root (Standard Gabriel) | [ ] YES / [ ] NO | |
| Windows NVMe | No wipe / no BitLocker mutation | [ ] confirmed | |
| Linux target wipe | Only with phrase `WIPE LINUX TARGET` if needed | [ ] understood | |

## Capture after BIOS update (Windows or Rescue)

```text
date -u
# From Windows: msinfo32 → BIOS Version/Date
# From Linux rescue:
sudo dmidecode -s bios-version
sudo dmidecode -s system-product-name
mokutil --sb-state || true
```

Paste outputs into a new evidence file:

`docs/evidence/rescue/install-assistant-001/G513QM_BIOS_GATE_<UTC>.md`

## Why

ROG Strix G-series reports ACPI/DPC stall and reboot issues fixed in newer BIOS builds; hybrid GPU + Secure Boot complicate NVIDIA module load. Armoury “iGPU only” removes the dGPU from the bus across boots.
