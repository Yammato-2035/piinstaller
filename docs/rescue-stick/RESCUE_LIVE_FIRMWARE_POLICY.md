# Rescue Live Firmware Policy

**Version:** 1.0 · **Scope:** Rescue Stick live environment (booted ISO)  
**Status:** Active for beta and release rescue builds

---

## 1. Purpose

Rescue boots a **Debian live** system with a controlled package set. Firmware and microcode updates on the live medium are restricted to avoid bricking hardware, breaking boot, or introducing unaudited blobs during field diagnostics.

---

## 2. Policy summary

| Rule | Policy |
|------|--------|
| Live session firmware flash | **Prohibited** (`destructive_blocked` class) |
| `fwupd` install on live | Disabled by package policy |
| Non-free firmware packages | Included at **ISO build time** only |
| Runtime `apt install` firmware | Blocked on rescue profile |
| Target disk firmware tools | Read-only advice only |

---

## 3. ISO build-time firmware

Firmware blobs (WiFi, GPU, etc.) are baked into the squashfs during controlled ISO build:

- Package list locked in rescue manifest (`RESCUE_REQUIRED_PACKAGE_POLICY_V2`).  
- Changes require controlled ISO build gate and evidence doc.  
- No post-ship `apt upgrade` on customer sticks without new ISO revision.

---

## 4. Live environment behavior

During live boot:

1. Kernel loads firmware from `/lib/firmware` in squashfs.  
2. `modprobe` may request missing firmware — log to evidence, do not auto-download.  
3. UI shows `explain_only` guidance if hardware lacks firmware (suggest built ISO variant).

---

## 5. UEFI / BIOS interaction

- Read firmware version via sysfs where available — **read-only**.  
- Do not call `dmidecode` output to telemetry (redacted summaries only).  
- No flashing utilities (`flashrom`, vendor tools) in live image package list.

---

## 6. QEMU / developer exception

Developer QEMU profiles may mount additional firmware volumes for lab reproduction. This exception does **not** apply to beta field sticks.

---

## 7. Safe actions related to firmware

| Action | Class |
|--------|-------|
| Explain missing firmware | `explain_only` |
| Suggest different ISO build | `target_readonly_advice` |
| Flash BIOS from stick | `destructive_blocked` |

---

## 8. Evidence

Missing firmware events logged under:

`/setuphelfer/evidence/hardware/firmware_*.json`

Include driver name and PCI ID class — not serial numbers.

---

## 9. Compliance check

Before ISO release:

- [ ] `fwupd` not in live package list  
- [ ] `flashrom` not in live package list  
- [ ] Firmware package versions pinned in manifest  
- [ ] Static check script passes (`R5A_PKFIX_FILESYSTEM_PACKAGES_CHECK` pattern)

---

## 10. Related documents

- `RESCUE_SAFE_ACTION_POLICY_V1.md`  
- `docs/evidence/rescue/RESCUE_REQUIRED_PACKAGE_POLICY_V2.md`  
- `RESCUE_BACKPORTS_KERNEL_PLAN.md`
