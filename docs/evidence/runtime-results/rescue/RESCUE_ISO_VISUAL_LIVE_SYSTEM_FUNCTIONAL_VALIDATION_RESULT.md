# Rescue ISO — Visual Live System Functional Validation (Operator)

**Klassifikation:** `live_boot_success_systemd_init_missing`  
**Rescue Runtime Functional:** **yellow** — Rescue gesamt: **yellow**

## Operator-Befund (VM, Ground Truth)

| Prüfung | Ergebnis |
|---------|----------|
| Login user/live | **ja** (Befehle ausgeführt) |
| `/opt/setuphelfer-rescue` | **ja** („Verzeichnis ist da“) |
| Keyboard | `KEYMAP=de-latin1` |
| Locale | `LANG=de_DE.UTF8` (Operator-Transkript) |
| Timezone | `Europe/Berlin` |
| Netzwerk | `eth0 does not exist` (Namensgebung: eher `ens3`/`enp*`) |
| **systemd PID 1** | **nein** — `System has not been booted with systemd as init system` |
| `systemctl` | fehlgeschlagen (kein D-Bus) |
| Backend `curl` | **Failed to connect** |

## Interpretation

- **Squashfs-Validator (offline) Exit 0** belegt Bundle, enabled Units und DE-Layout **im Image**.
- Im **laufenden Live-System** ist **systemd nicht Init** → `multi-user.target.wants`-Units starten nicht → kein Rescue-Backend auf `:8000`.
- Abweichung Image vs. Runtime — kein Fake-Green.

## Nicht geprüft / Host

Kein Test auf Host `volker-ROG-Strix` unter `/opt/setuphelfer`.

## Nächster Schritt

**`RESCUE_ISO_VM_SYSTEMD_INIT_TRIAGE`** — warum Live ohne systemd als PID 1 bootet; ggf. Build-Tree (`systemd`/`systemd-sysv`, live-boot init).

JSON: `rescue_iso_visual_live_system_functional_validation_result_latest.json`
