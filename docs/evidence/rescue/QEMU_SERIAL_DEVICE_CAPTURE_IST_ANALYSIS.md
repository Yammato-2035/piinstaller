# QEMU Serial Device Capture — IST Analysis

**Run:** `qemu_rescue_developer_serial_20260601_160824`
**HEAD (analysis):** `2091262`

## Exakte QEMU-CMD (Lauf 160824)

```
timeout 1200 qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -smp 2 \
  -cdrom …/binary.hybrid.iso -boot d -snapshot -no-reboot \
  -serial file:…/qemu-serial.log -monitor none \
  -nic user,model=virtio-net-pci -display none
```

## Serial / Display / Monitor

| Argument | Wert |
|----------|------|
| Serial | `-serial file:<path>` (legacy shorthand) |
| `-nographic` | **nicht** verwendet |
| `-monitor` | `none` |
| `-display` | `none` (Autopilot) |
| `isa-serial` explizit | **nein** |
| Stderr | `qemu-gtk-stderr.log` — `terminating on signal 15 … (timeout)` |

## Serial-Datei

| Feld | Wert |
|------|------|
| Pfad | `docs/evidence/runtime-results/rescue/qemu/…/qemu-serial.log` |
| Größe | **0** Bytes |
| Vor Start geleert | yes (`: >` im Skript) |
| Beschreibbar | yes (Datei existiert) |

## Bewertung `-serial file:` vs. chardev + isa-serial

| Aspekt | `-serial file:` | chardev + isa-serial |
|--------|-----------------|----------------------|
| COM1 (0x3f8) | meist ja | explizit |
| Signal handling | `signal=off` nicht gesetzt | `signal=off` empfohlen |
| QEMU-Empfehlung | älter | robuster für Datei-Logs |

**Alleine** reicht der Wechsel vermutlich **nicht**: Bei `timeout 0` + `vesamenu` + `-display none` bootet der Kernel vermutlich **nie** — daher kein ttyS0-Output.

## Wahrscheinliche Ursachen (priorisiert)

1. **ISOLINUX `timeout 0`** — Menü wartet unbegrenzt; ohne Tastatur/Eingabe kein Boot.
2. **`default vesamenu.c32`** — grafisches Menü bei `-display none` nicht bedienbar.
3. **Kein `SERIAL 0 115200` in ISOLINUX** — Bootloader schreibt nicht auf COM1.
4. **`-serial file:`** — sekundär; nach Bootloader-Fix erneut mit chardev verifizieren.

## Fleet-Snapshot (160824)

- `serial.path` leer, `qemu.exit_code` null im API-Snapshot (Finish unvollständig)
- Skript meldete KVM aktiv; Fleet `kvm_enabled: false` (Telemetry-Lücke, separat adressiert)
