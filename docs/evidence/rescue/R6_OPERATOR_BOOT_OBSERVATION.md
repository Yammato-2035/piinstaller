# R.6 — Operator Boot-Beobachtung

**Anleitung:** Nach MSI-Boot die Spalte „Beobachtung“ ausfüllen. Foto/Video optional unter `docs/evidence/rescue/media/` ablegen (ohne Seriennummern).

| # | Frage | Beobachtung | ja/nein/unbekannt |
|---|-------|-------------|-------------------|
| 1 | Wird der Stick im MSI-Bootmenü angezeigt? | | |
| 2 | Wird **UEFI: SETUPHELFER** angezeigt? | | |
| 3 | Wird GRUB angezeigt? | | |
| 4 | Grafisches GRUB oder Text-GRUB? | | |
| 5 | Setuphelfer-Logo sichtbar? | | |
| 6 | Menüeintrag „Setuphelfer Rettung starten“ sichtbar? | | |
| 7 | Startet Linux nach Auswahl? | | |
| 8 | Gibt es Kernel-/Initrd-Ausgabe? | | |
| 9 | Bleibt Boot hängen? | | |
| 10 | Wird TUI angezeigt? | | |
| 11 | Wird Browser/Kiosk angezeigt? | | |
| 12 | Gibt es eine Shell? | | |
| 13 | Gibt es Fehlermeldungen? | | |
| 14 | Foto/Video vorhanden? | | |

## Klassifikation (eine Option ankreuzen)

- [ ] `no_boot_device` — Stick/UEFI-Eintrag fehlt (A)
- [ ] `grub_not_loaded` — UEFI startet, GRUB nicht (B partial)
- [ ] `grub_loaded_linux_failed` — GRUB ok, Kernel/Initrd scheitert (B)
- [ ] `linux_booted_no_menu` — Linux läuft, kein TUI/Kiosk (C)
- [ ] `menu_loaded_no_persistence` — UI startet, `/setuphelfer-evidence/` fehlt (D)
- [ ] `persistence_path_failed` — Evidence nur RAM oder Schreibfehler (E/F)
- [ ] `boot_success_evidence_missing` — Boot ok, `boot/boot_marker.md` fehlt trotz Hook (R.6 nicht erfüllt)
- [ ] `boot_success` — `setuphelfer-evidence/boot/boot_marker.md` auf Stick vorhanden

## Notizen

_(frei)_
