# 10 – USB Update Result

| Feld | Wert |
|------|------|
| Updater | `update-fat32-esp-live-payload.sh --execute-update` |
| Status | **success** / verify **success** |
| Exit | 0 |
| Bestätigung 1+2 | akzeptiert |
| SquashFS nach Write | `3706b824a8992b8abf8d9e20a6d1daa47503cb7c3fada9ac5189e38c2b9ef43e` |
| GRUB nach Write | `68649d4dab94a19c4ead0acbe060902d215fb36b4b13ffa5ef27d9f195931030` (ensure_tui_input_diagnostic_menuentry) |
| Kernel/Initrd | unverändert |
| Temporäre `.sqtmp`/`.new` | keine |
| SETUP_LOGS | erhalten (weiterhin gemountet, Inhalt nicht gelöscht) |
| Partitionslayout | unverändert (sda1+sda2) |
