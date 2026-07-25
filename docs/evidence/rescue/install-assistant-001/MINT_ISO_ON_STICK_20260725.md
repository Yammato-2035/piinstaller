# Mint ISO auf Rettungsstick — Gabriel only

## Ergebnis

| Feld | Wert |
|------|------|
| Volume | `SETUP_LOGS` (`/dev/sda2`) |
| Pfad | `setuphelfer/iso-cache/linux_mint/linuxmint-22.2-cinnamon-64bit.iso` |
| Version | Linux Mint **22.2** Cinnamon 64-bit |
| Größe | ~2,9 GiB |
| SHA256 | `759c9b5a2ad26eb9844b24f7da1696c705ff5fe07924a749f385f435176c2306` |
| Verify | **OK** (match `sha256sum.txt` von mirrors.kernel.org) |
| Mirror | `https://mirrors.kernel.org/linuxmint/stable/22.2` |
| ESP-Pointer | `SETUPHELFER/setuphelfer/rescue/mint_iso_on_stick.json` |

## Nicht auf Entwickler-Laptop installieren

Zielmaschine: **Gabriel G513QM**. Host G713PI bleibt unberührt.

## Nutzung auf Gabriel

1. Vom gepatchten Stick booten (Default: Linux-Installation GUI).
2. Assistent liest ISO unter `SETUP_LOGS/.../iso-cache/linux_mint/`.
3. SHA256 muss `valid` sein → Handoff auf `linux_target`.
