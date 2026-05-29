# Followup-Plan

## Profil 1 — Headless extended (ausgeführt)

```bash
export VM_BOOT_TIMEOUT_TRIAGE_FREIGEGEBEN=1
ISO_PATH="…/binary.hybrid.iso"
timeout 600 qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" -boot d -snapshot -no-reboot -nographic \
  > /tmp/setuphelfer_rescue_vm_boot_timeout_triage_stdout.log \
  2> /tmp/setuphelfer_rescue_vm_boot_timeout_triage_stderr.log || true
```

## Profil 2 — Operator visual (Handoff)

```bash
qemu-system-x86_64 -m 2048 -smp 2 -cdrom "$ISO_PATH" -boot d -snapshot -no-reboot
```

Kein `-hda`, kein USB, kein Host-Disk.

JSON: `rescue_iso_vm_boot_timeout_followup_plan_latest.json`
