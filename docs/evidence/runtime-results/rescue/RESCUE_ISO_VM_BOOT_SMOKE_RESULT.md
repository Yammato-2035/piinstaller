# Rescue ISO VM Boot Smoke — Result

**Datum:** 2026-05-29  
**Ausgeführt:** **ja** (ein Lauf, 120 s Timeout)  
**Freigabe:** `VM_BOOT_SMOKE_FREIGEGEBEN=1` für diesen STRICT-MODE-Operator-Lauf gesetzt

## Command Safety

| Prüfung | Ergebnis |
|---------|----------|
| `-hda` / `-drive` | **nein** |
| Host-Disk `/dev/*` | **nein** |
| USB-Passthrough | **nein** |
| Nur `-cdrom` ISO | **ja** |

## QEMU

```text
timeout 120 qemu-system-x86_64 -m 2048 -smp 2 -cdrom "$ISO_PATH" -boot d \
  -snapshot -no-reboot -serial stdio -display none
```

| | |
|---|---|
| **Exit** | **124** (timeout) |
| **stdout** | **0** Bytes |
| **stderr** | 71 Bytes — `terminating on signal 15 … (timeout)` |

## Klassifikation

**`timeout_no_boot_signal`** — kein isolinux/kernel/live/setuphelfer-Marker in den Logs.

**Nicht behauptet:** Boot-Erfolg, Live-System-Start, USB-tauglicher Stick.

## Hinweis

User nicht in Gruppe `kvm` → TCG ohne Beschleunigung; 120 s können für ersten Serial-Output zu kurz sein. Nächster Schritt: **`RESCUE_ISO_VM_BOOT_TIMEOUT_TRIAGE`** (längerer Timeout, `-nographic`, oder Operator mit KVM).

JSON: `rescue_iso_vm_boot_smoke_result_latest.json`
