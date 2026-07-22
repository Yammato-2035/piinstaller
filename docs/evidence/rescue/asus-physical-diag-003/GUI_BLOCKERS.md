# Was die grafische Oberfläche blockiert (G513QM)

## Kurzurteil

Auf dem erfolgreichen Diagnose-Boot **21:08** war die GUI **absichtlich aus** (`setuphelfer_mode=text` + `hardware_discovery` skippt GUI) und zusätzlich durch **`nomodeset`** technisch unmöglich (nur EFI-Framebuffer).

Das ist **kein fehlender ASUS-Windows-Treiber**.

## Schichten

| Blocker | Typ | Beleg |
|---|---|---|
| `setuphelfer_mode=text` | Policy | boot_state, cmdline |
| `hardware_discovery_skip_gui` | Policy | entrypoint |
| `nomodeset` | Kernel | dmesg: only system framebuffer; `/proc/fb`=EFI VGA |
| nouveau blacklist | Safety | cmdline |
| Vorher ohne nomodeset | Historisch | amdgpu → dummy console, schwarzes Panel |
| Kein proprietary NVIDIA | Erwartet | Rescue-Image |

## Folge

- TUI/Text: **ja** (dieser Boot)
- GUI/Kiosk: **nein** (by design + nomodeset)
- Für Diagnose ausreichend; GUI braucht eigenen, getesteten Lab-Eintrag ohne nomodeset.
