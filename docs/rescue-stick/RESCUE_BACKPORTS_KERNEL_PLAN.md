# Rescue Backports Kernel Plan

**Version:** 1.0 · **Decision record:** `docs/evidence/rescue/RESCUE_BACKPORTS_KERNEL_DECISION_V2.md`  
**Current state:** Backports kernel **disabled** (`backports_enabled: false`)

---

## 1. Context

Rescue Stick images normally track **Debian stable** `linux-image-amd64` for predictable drivers and reproducible ISO builds. Debian backports kernels offer newer hardware support but increase risk for live ISO validation, squashfs size, and QEMU smoke matrix.

---

## 2. Current decision (V2)

| Field | Value |
|-------|-------|
| `backports_enabled` | `false` |
| Default kernel | `linux-image-amd64` (stable) |
| Evidence requirement | SquashFS package manifest before any backports claim |

Rationale: avoid unverified backports claims in release notes; keep single kernel path in test matrix.

---

## 3. When backports may be reconsidered

Triggers for a new decision record (`V3+`):

1. Stable kernel lacks driver for **approved** beta hardware class (documented in diagnostics DB).  
2. QEMU and physical smoke pass on backports-enabled trial ISO.  
3. Controlled ISO build gate approves package list delta.  
4. SquashFS size within USB partition budget.

---

## 4. Evaluation procedure

```
1. Add linux-image-amd64-backports to trial manifest only
2. Rebuild squashfs → record package list hash
3. Run R5A boot path static check + QEMU serial smoke
4. Physical stick boot on ≥2 NIC/WiFi classes
5. File RESCUE_BACKPORTS_KERNEL_DECISION_V3.json + .md
6. If fail → revert manifest, keep backports_enabled false
```

---

## 5. Build integration

| Stage | Location |
|-------|----------|
| Package list | Rescue ISO build manifest (private overlay) |
| GRUB entries | Default boot → stable; optional trial entry `rescue-backports` (dev only) |
| Version pin | Same as `config/version.json` rescue slice |

---

## 6. Runtime behavior (if enabled in future)

- GRUB default remains stable unless operator selects backports entry.  
- Telemetry records `kernel_variant: stable|backports` in assessment metadata.  
- No runtime kernel switch — reboot required.

---

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Larger initramfs | Partition size check in RS_P2C verify |
| DKMS modules break | Exclude DKMS from live image |
| Test matrix explosion | Separate decision per rescue version |
| Security CVE lag | Monitor Debian security announcements |

---

## 8. Relationship to firmware policy

Backports kernel does **not** replace `RESCUE_LIVE_FIRMWARE_POLICY.md`. Firmware blobs remain ISO-build-time only.

---

## 9. Developer QEMU profile

QEMU developer ISO may use host kernel passthrough for speed — not comparable to stick backports decision. Document QEMU profile separately.

---

## 10. Related documents

- `RESCUE_BOOT_ARCHITECTURE.md`  
- `RESCUE_CONTROLLED_ISO_BUILD_PERMISSION_POLICY.md`  
- `docs/evidence/rescue/RESCUE_BACKPORTS_KERNEL_DECISION_V2.json`
