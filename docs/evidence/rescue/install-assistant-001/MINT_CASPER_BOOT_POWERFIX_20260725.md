# Mint-Installer bootet nicht / kein Ausschalten — Fix 2026-07-25

## Diagnose (Gabriel G513QM, 14:12)

- Boot landete wieder im Rescue-Text (`setuphelfer_mode=text`)
- Auto-Discovery + Hardware-Discovery liefen parallel → TUI/Poweroff blockiert
- ISO-Loopback-GRUB war unzuverlässig (kein Casper-Boot in Evidence)

## Fix auf Stick

1. **Mint casper extrahiert** nach `SETUP_LOGS/mint-live/` (vmlinuz, initrd.lz, filesystem.squashfs)
2. **GRUB Default** = `Linux Mint 22.2 Installer (direkt vom Stick)` — kein ISO-Loopback
3. GRUB-Einträge **Neustart (sofort)** / **Ausschalten (sofort)** (`reboot`/`halt`)
4. TUI: Force-Poweroff (`systemctl poweroff -i --force --force` / sysrq)
5. Auto-Discovery: `ConditionKernelCommandLine=!setuphelfer_install_assistant=1`

## Bedienung jetzt

1. Falls Gerät hängt: **Power-Taste ~10 s** halten
2. Vom Stick booten → **Default startet Mint-Installer direkt**
3. Falls Menü sichtbar: unten **Ausschalten (sofort)** wählen
4. Im Mint-Installer nur die Linux-Ziel-NVMe wählen (nicht Windows)
