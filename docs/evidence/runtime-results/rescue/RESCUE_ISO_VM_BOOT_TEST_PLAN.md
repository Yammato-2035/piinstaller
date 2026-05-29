# Rescue ISO — VM Boot Test Plan

**ISO:** `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`  
**SHA256:** `03d5aa95ba5e63f603a13bc7ec8765156aadddf3f8e7b6946c0bb08f9aba31f6`  
**Volume:** `SETUPHELFER_RESCUE`

## VM-Parameter

| Parameter | Wert |
|-----------|------|
| Backend | `qemu-system-x86_64` |
| RAM | 2048 MB |
| CPU | 2 |
| Boot | BIOS/SeaBIOS, `-boot d` (CD-ROM) |
| Virtuelle Festplatte | **nein** |
| Host-Disk | **verboten** |
| USB-Passthrough | **verboten** |
| Netzwerk | optional `-nic none` oder NAT-only |
| Timeout | 120 s |

## Operator-Freigabe

VM-Smoke nur bei gesetztem **`VM_BOOT_SMOKE_FREIGEGEBEN`** (Umgebung oder expliziter Prompt).

## Beispiel-Befehl (Plan — nicht ohne Freigabe ausführen)

```bash
ISO_PATH="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
timeout 120 qemu-system-x86_64 \
  -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" -boot d \
  -snapshot -no-reboot \
  -serial stdio -display none \
  > /tmp/setuphelfer_rescue_vm_boot_stdout.log \
  2> /tmp/setuphelfer_rescue_vm_boot_stderr.log || true
```

**Verboten:** `-hda`, `-drive file=/dev/...`, USB, `losetup`, ISO rw-mount.

## Erfolgskriterien

1. VM startet vom ISO  
2. Bootloader oder Kernel-Ausgabe auf Serial  
3. Live-System erreicht Login/Prompt/UI/Setuphelfer-Einstieg  
4. Kein Host-Datenträger eingebunden  
5. Kein Schreibzugriff auf Host  

## Fehlerkriterien

Bootloader fehlt, Kernel panic, initramfs-Hang, Bundle fehlt, ISO in VM nicht bootfähig.

JSON: `rescue_iso_vm_boot_test_plan_latest.json`  
Policy: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`
