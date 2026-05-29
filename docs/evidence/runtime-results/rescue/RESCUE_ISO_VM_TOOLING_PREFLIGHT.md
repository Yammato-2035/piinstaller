# Rescue ISO — VM Tooling Preflight (read-only)

**Kein** `apt install`, **kein** Tooling-Setup in diesem Lauf.

| Tool | Status |
|------|--------|
| `qemu-system-x86_64` | **ja** (`/usr/bin`, QEMU 8.2.2) |
| `qemu-system-i386` | **ja** |
| `/dev/kvm` | vorhanden |
| User in `kvm` | **nein** (TCG-Fallback möglich, langsamer) |
| `VBoxManage` | **ja** (7.0.16) |
| User in `vboxusers` | **ja** |

**Empfehlung:** `qemu-system-x86_64` mit `-serial stdio -display none` (headless).  
**vm_boot_test_possible_without_install:** **true**  
**requires_operator_decision:** **true** (Smoke nur mit `VM_BOOT_SMOKE_FREIGEGEBEN`)

JSON: `rescue_iso_vm_tooling_preflight_latest.json`
