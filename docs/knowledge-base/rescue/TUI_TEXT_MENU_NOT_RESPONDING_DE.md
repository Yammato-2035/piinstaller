# Wissensbasis: Textmenü reagiert nicht (DE)

## Symptom

GRUB bedienbar, Textmenü sichtbar, Tastatur im Menü ohne Wirkung. Oft hohe CPU bei `whiptail`.

## Sofortmaßnahme

GRUB-Eintrag **TUI-Eingabediagnose (read-only)** booten und Assistenten auf tty2 folgen.
Kein Backup/Restore starten.

## Typische Hypothesen

- H7: newt/Redraw-/Poll-Loop
- H4: Terminalzustand
- FD-Mismatch (stdin nicht tty1)
- H6: Kernel/Input (seltener, wenn GRUB und HID-Devices ok)

## Ergebnis

Evidence auf SETUP_LOGS auswerten; Reparatur erst nach bestätigter Hypothese.
