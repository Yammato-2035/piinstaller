# 02 – Build-Modus-Entscheidung

## Entscheidung: **payload_repack**

### Begründung

| Kriterium | Bewertung |
|-----------|-----------|
| Kernel geändert? | nein |
| Initramfs geändert? | nein |
| Neue Live-Pakete nötig? | nein |
| Neue Dateien in SquashFS injizierbar? | ja (`rescue_*.py`, CLI, Unit, TUI-Guard) |
| systemd Enablement per Repack? | ja (Wants-Symlink im Inject) |
| GRUB über bestehenden Inject-/Updaterpfad? | ja (`ensure_tui_input_diagnostic_menuentry` / GUI-interactive Patcher) |
| Offizieller Repack-Pfad | `scripts/rescue/inject-gui-bvr-fixes-into-stick-squashfs.sh` |
| Offizieller USB-Updater | `scripts/rescue-live/update-fat32-esp-live-payload.sh` (Plan/Execute, atomar) |

### Nicht gewählt

- `controlled_live_build` — unnötig (kein Kernel/Paketbedarf).
- `blocked` — Tools (`unsquashfs`/`mksquashfs`) vorhanden.

### Verfahren

1. ESP read-only mounten, SquashFS in Host-Staging kopieren.
2. Inject gegen **Staging-ESP** (nicht direkt Stick) → neues SquashFS-Artefakt.
3. Inhalts-/GRUB-Audit am Artefakt.
4. Nach Doppelbestätigung: offizieller FAT32-ESP-Payload-Updater + GRUB-Diagnose-Eintrag.
