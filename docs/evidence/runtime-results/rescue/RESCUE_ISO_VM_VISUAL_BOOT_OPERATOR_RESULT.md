# Rescue ISO — Visueller VM-Boot (Operator)

**Profil:** `visual_operator`  
**Freigabe:** `LIVE_BOOT_VISUAL_FREIGEGEBEN=1`  
**Klassifikation:** **`live_system_started`**

## Command (Operator)

```bash
qemu-system-x86_64 -m 2048 -smp 2 -cdrom "$ISO_PATH" -boot d -snapshot -no-reboot
```

Kein `-hda`, kein `-drive`, kein USB.

## Beobachteter Boot (Screenshot-Ground-Truth)

| Stufe | Ergebnis |
|-------|----------|
| Kernel / Initrd | ja (Linux-Bootmeldungen) |
| Live-System | **Debian GNU/Linux 12**, Hostname `debian` |
| Netzwerk | DHCP **10.0.2.15** auf `ens3` |
| Runlevel | **2** |
| Login-Prompt | **`debian login:`** |
| Setuphelfer-Bundle/UI | **nicht** in dieser Ansicht belegt |

## Nebenbefunde (nicht blockierend)

- `smartd` start fehlgeschlagen — in VMs ohne echte SMART-Disk üblich.
- Operator: Login als **`root`** zweimal → **Login incorrect** (erwartbar; Debian-Live nutzt oft User **`live`**, nicht root-Konsole).

## Abgrenzung

- **Bootloader** (nographic Serial) ≠ **Live-System** — visuell jetzt belegt.
- VM-Live-Boot ≠ USB-/Hardware-Boot.
- Rescue bleibt **yellow** bis Setuphelfer-Funktionscheck.

**Nächster Schritt:** `RESCUE_ISO_LIVE_SYSTEM_FUNCTIONAL_VALIDATION` (Login `live`, `/opt/setuphelfer-rescue`, Backend localhost).

JSON: `rescue_iso_vm_visual_boot_operator_result_latest.json`
