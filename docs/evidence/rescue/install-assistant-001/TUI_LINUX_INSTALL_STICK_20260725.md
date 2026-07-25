# TUI Linux-Installation auf Stick (Gabriel)

## Diagnose 2026-07-25 13:56 (G513QM)

- Boot mit `setuphelfer_mode=gui` + Install-Flags
- GUI → Fallback Text: Rescue-UI HTML fehlt (`frontend_missing`)
- Altes TUI ohne Linux-Install-Eintrag

## Fix auf Stick

- Squashfs gepatcht: TUI-Menü **„Linux-Installation (Mint vom Stick)“** oben
- Helper `setuphelfer-rescue-tui-linux-install`
- GRUB Default = **Linux-Installation (Text)**
- Neuer GRUB-Eintrag **„Linux Mint 22.2 Installer (ISO vom Stick)“** (loopback SETUP_LOGS)

## Bedienung auf Gabriel

1. Stick booten → Default Text-Assistent **oder**
2. Direkt **Linux Mint 22.2 Installer (ISO vom Stick)** wählen
3. Im TUI: Menüpunkt Linux-Installation → bestätigt Neustart in Mint-Installer
4. Im Mint-Installer nur die Linux-Ziel-NVMe wählen (nicht Windows)
