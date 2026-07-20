# Knowledge base: Text menu not responding (EN)

## Symptom

GRUB works, text menu is visible, keyboard does nothing in the menu. Often high `whiptail` CPU.

## Immediate action

Boot GRUB entry **TUI input diagnostic (read-only)** and follow the tty2 assistant.
Do not start backup/restore.

## Typical hypotheses

- H7: newt redraw/poll loop
- H4: terminal state
- FD mismatch (stdin not tty1)
- H6: kernel/input (less likely if GRUB and HID devices work)

## Outcome

Review SETUP_LOGS evidence; repair only after a confirmed hypothesis.
