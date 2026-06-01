# QEMU Serial Capture and Bootloader Output Contract

**Scope:** `developer-qemu` rescue profile and `run-qemu-developer-iso-smoke.sh`.

## QEMU (host)

| Requirement | Implementation |
|-------------|----------------|
| Default capture | `-chardev file,id=charserial0,path=<log>,signal=off` + `-device isa-serial,chardev=charserial0` |
| Legacy opt-in | `--serial-backend legacy-file` → `-serial file:<log>` |
| Monitor | `-monitor none` (unchanged) |
| Headless | `-display none` allowed; **no** `-nographic` (stdout/stderr mix) |
| Serial log prep | `mkdir -p`; `: > log` before QEMU; fail if not writable |
| Evidence | `qemu_serial_capture_meta.json` in run dir |
| Fleet finish | `serial.path`, `serial.size_bytes`, `qemu.exit_code`, `kvm` / `acceleration` |

## Bootloader (ISO build tree)

### ISOLINUX (BIOS / `-boot d` CD)

| Directive | Value |
|-----------|--------|
| `SERIAL` | `0 115200` |
| `CONSOLE` | `0` |
| `PROMPT` | `0` |
| `TIMEOUT` | `30` (3 s) |
| `DEFAULT` / `ONTIMEOUT` | `live-` |
| Menu | **No** `vesamenu.c32` default (avoids headless hang) |

### GRUB (EFI, if present after `lb build`)

Prepended via `095-developer-qemu-grub-serial.hook.binary`:

```
serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
terminal_input serial console
terminal_output serial console
set timeout=3
```

### Kernel `append` (developer-qemu)

```
console=tty0 console=ttyS0,115200n8 loglevel=7 systemd.log_level=debug systemd.show_status=true ignore_loglevel printk.devkmsg=on
```

**No** `quiet` / `splash` in developer-qemu live append.

## Release profiles

Standard / non-`developer-qemu` profiles keep Debian live-build ISOLINUX defaults (`timeout 0`, vesamenu) unless explicitly changed elsewhere.

## Verification order

1. `prepare-controlled-live-build-tree.sh` with `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`
2. Controlled ISO rebuild
3. Static ISO strings + tree checks
4. Exactly one QEMU serial smoke (no retry loop in same task)
