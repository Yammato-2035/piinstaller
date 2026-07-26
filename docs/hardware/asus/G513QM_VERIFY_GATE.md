# Verify gate — before next Gabriel physical install

Do not boot Gabriel for install until **all** items are YES.

## Pre-flight

| # | Check | How | OK? |
|---|--------|-----|-----|
| 1 | BIOS gate filled | [`G513QM_OPERATOR_BIOS_GATE.md`](G513QM_OPERATOR_BIOS_GATE.md) all YES | [ ] |
| 2 | Failure matrix current | [`G513QM_FAILURE_MATRIX.md`](G513QM_FAILURE_MATRIX.md) | [ ] |
| 3 | Stick pack present | `SETUP_LOGS/setuphelfer/rog-pack/g513qm/MANIFEST.json` | [ ] |
| 4 | Pack SHA integrity | `python3 -c` verify file hashes vs MANIFEST (or `sha256sum -c`) | [ ] |
| 5 | NVIDIA debs ~18 slim | `ls SETUP_LOGS/.../debs/nvidia/*.deb \| wc -l` ≈ 18, size ~380M | [ ] |
| 6 | GRUB default Rescue | First menuentry Rescue-Root; no MSI E2E default | [ ] |
| 7 | Scripts reachable | `bash .../install-from-rescue.sh --help` | [ ] |

## During / after install (evidence to capture)

Create `G513QM_VERIFY_<UTC>.md` with:

```bash
date -u
dmidecode -s bios-version
dmidecode -s system-product-name
lsblk -o NAME,SIZE,MODEL,SERIAL,LABEL,FSTYPE,MOUNTPOINT
# After first boot of installed system:
inxi -SMGx || true
lsmod | egrep 'amdgpu|nvidia|nouveau|asus' || true
dkms status || true
journalctl -b -p err --no-pager | tail -80
test -f /var/lib/setuphelfer/rog-pack-applied && cat /var/lib/setuphelfer/rog-pack-applied
```

## Pass criteria

- Rescue boots with usable console (already proven).
- Ubiquity or documented fallback installs **only** linux_target; Windows untouched.
- First boot applies ROG pack (marker file) or operator ran `apply-rog-pack.sh` manually.
- Either text console stable **or** desktop via iGPU profile; NVIDIA only after pack + `postinstall-nvidia-prime` profile.
- No kernel panic / keyboard soft-power on basic login for the chosen profile.

## Fail → stop

Any new hang/panic: append row to failure matrix; **do not** invent new GRUB experiments outside the matrix.
