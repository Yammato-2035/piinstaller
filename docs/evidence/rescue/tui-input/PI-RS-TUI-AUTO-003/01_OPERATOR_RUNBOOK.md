# 01 – Operator-Runbook PI-RS-TUI-AUTO-003

## Hardware bereithalten

- MSI GE63 Raider RGB 8RF / MS-16P5
- Setuphelfer-Stick **1.10.0.59** (Intenso Ultra Line)
- optional: kabelgebundene USB-Tastatur
- optional: Smartphone/Kamera

## Vor dem Einschalten

1. Am Dev-PC: Stick sauber aushängen (`SETUP_LOGS` / ESP), physisch entfernen.
2. Stick **nur** in den MSI stecken.
3. Keine zusätzlichen USB-Datenträger.
4. Externe Tastatur **zunächst nicht** anschließen.
5. Kein LAN nötig; keine Passwörter; keine internen Disks auswählen.

## GRUB

1. MSI vom Stick booten, auf GRUB warten.
2. Mit **interner** Tastatur wählen:

```text
Setuphelfer – TUI-Eingabediagnose (read-only)
```

3. Enter.

Dokumentieren:

| Beobachtung | ja/nein/unbekannt |
|-------------|-------------------|
| GRUB sichtbar | |
| Interne Pfeiltasten in GRUB | |
| Enter in GRUB | |
| Caps-/Num-Lock in GRUB | |
| Diagnoseeintrag vorhanden | |
| Diagnoseeintrag bootet | |

Wenn GRUB intern nicht bedienbar: externe Tastatur testen → Lauf = `grub_input_failure` (kein regulärer TUI-Test).

## tty2-Diagnose

Erwartung: tty1 = normale TUI, tty2 = Diagnoseassistent.

| Check | ja/nein |
|-------|---------|
| Diagnoseoberfläche sichtbar | |
| lesbar | |
| Tastatur auf tty2 | |

Falls nach 90 s nichts: einmal `Ctrl+Alt+F2`. Keine weiteren Reparaturversuche → sonst `diagnostic_ui_not_reached`.

## Interne Tastatur (tty2)

Assistenten folgen. Tasten einzeln, nicht mehrfach:

```text
Pfeil hoch, Pfeil runter, Tab, Escape, Enter, A, Caps/Num Lock
```

## tty1-Menütest

Nur wenn Assistent Guard bestätigt (`write_actions_blocked` etc.).

Auf tty1 (nach Assistenten-Ansage), je ~2 s Pause:

```text
Pfeil runter, Pfeil hoch, Tab, Escape, Enter
```

Beobachten: Markierung / Flackern / Redraw / Enter-Dialog / Escape / unverändertes Bild.

Automatische Rückkehr zu tty2 erwarten. Sonst einmal `Ctrl+Alt+F2` → `automatic_vt_return_failed`.

## Operatorfragen auf tty2

Antworten nur: **J** / **N** / **U**

- Menümarkierung bewegt?
- Menü geflackert?
- Menü neu gezeichnet?
- Enter hat etwas geöffnet?
- Escape reagiert?
- Bild unverändert?
- Tastatur tty2 OK?
- Tastatur tty1 OK?

## Externe USB-Tastatur (optional)

Nur nach Assistenten-Aufforderung anschließen. Sonst:

```text
external_keyboard_test=skipped_not_available
```

## Evidence & Shutdown

- Evidence unter `SETUP_LOGS/tui-input-diagnostics/<RUN_ID>/`
- Assistent: Evidence finalisieren lassen (Manifest + SHA256SUMS)
- Auto-Shutdown ist aus → bei Frage sicher herunterfahren mit **J**
- Kein Backup/Restore/Reboot über normales TUI-Menü

## Danach

1. Stick entfernen, am Dev-PC einstecken.
2. Im Chat melden: **STICK ZURÜCK – IMPORT STARTEN**
3. Agent importiert, analysiert, entscheidet Hypothese/Reparaturpfad — **ohne Fix**.

## Verboten während des Laufs

`stty sane`, `reset`, `kill`/`pkill`, Unit-Neustarts, GRUB/Payload-Änderung, Backup/Restore, interne Disks mounten/schreiben.
