# G513QM Kernel A/B/C Control Matrix

**Purpose:** Distinguish Setuphelfer/boot fault vs kernel regression vs BIOS/firmware vs hardware — without installing Linux or writing internal NVMe.

## Controls

| ID | Image | Modified | Kernel expectation | Role |
|----|-------|----------|--------------------|------|
| A | Official Linux Mint 22.1 Cinnamon ISO | **no** | 6.8-family (verify after boot) | Baseline older HWE |
| B | Official Linux Mint 22.3 Cinnamon ISO | **no** | as shipped (verify after boot) | Unmodified current Mint |
| C | Setuphelfer diagnostic casper (mint-live + lab services) | **yes** (lab only) | not forced to stay on 6.14.0-29; document closure | Out-of-band KMS capture |

## Control A rules

- Unmodified official ISO only after `verified` or `checksum_only` with good GPG on sha256sum.txt
- No Setuphelfer GRUB, packs, or `rescue.target`
- Prefer separate USB medium
- Boot to desktop max; no install

## Control B rules

Same as A for Mint 22.3.

## Control C rules

```text
systemd.unit=multi-user.target
systemd.debug-shell=1   # tty9, no sulogin
NO rescue.target
AMDGPU blacklisted until manual setuphelfer-gpu load-amdgpu
NVIDIA/nouveau blacklisted for AMD-only runs
ignore_loglevel log_buf_len=8M drm.debug=0x1ff
early local capture + netconsole (wired LAN)
```

### Parameter single-runs (never combine)

| Run | Profile id | Extra |
|-----|------------|-------|
| C1 | g513qm_control_c1_standard | none |
| C2 | g513qm_control_c2_dc0 | amdgpu.dc=0 |
| C3 | g513qm_control_c3_aspm0 | amdgpu.aspm=0 |
| C4 | g513qm_control_c4_recovery | amdgpu.gpu_recovery=1 |

## Media strategy

Prefer three USBs. If one stick: write → test → copy evidence off → rewrite. No Ventoy unless proven not to alter cmdline/Secure Boot path.

## USB write gate

Device identity (model/serial/UUID/label) · exclude internal NVMe · ISO SHA256 · operator intent · prior evidence saved · post-write partition/readback hash.

## Decision pointer

See `docs/evidence/rescue/g513qm-kernel-abc/G513QM_CONTROL_RESULT_DECISION.md`.
