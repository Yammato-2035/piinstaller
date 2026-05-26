# Rescue ISO Build Dependencies

## rsvg vs. rsvg-convert

Für den aktuellen Debian-`live-build`-Pfad mit `lb_binary_syslinux` und dem Theme `live-build` reicht es nicht, nur `rsvg-convert` zu haben. Das Skript prüft explizit auf `/usr/bin/rsvg` und ruft anschließend `rsvg --format png --height 480 --width 640 ...` auf.

`librsvg2-bin` liefert auf dem Host jedoch standardmäßig `rsvg-convert`, nicht automatisch einen Legacy-Befehl `rsvg`.

## Was daraus folgt

- Fehlt `librsvg2-bin` beziehungsweise `rsvg-convert`, ist das ein echter Host-Dependency-Blocker.
- Ist `rsvg-convert` vorhanden, darf das **nicht** mehr als „Paket fehlt“ fehlklassifiziert werden.
- Wenn `live-build` trotzdem den Legacy-Befehl `rsvg` verlangt, ist das ein eigener Kompatibilitätszustand.

## Warum kein globaler Symlink empfohlen wird

Ein globaler Symlink nach `/usr/bin/rsvg` würde Systemzustand verändern und außerhalb des kontrollierten Rescue-Repo-Kontexts wirken. Das ist für Setuphelfer ausdrücklich unerwünscht.

Stattdessen wird ein projektlokaler Wrapper verwendet:

- Pfad: `build/rescue/tool-compat/bin/rsvg`
- Zweck: delegiert kontrolliert auf `rsvg-convert`
- Nutzung: nur über explizit erweiterten `PATH` für den späteren Operator-Build

## Warum Setuphelfer nichts automatisch installiert

Setuphelfer startet weder automatisch `apt install` noch ändert er globale Host-Binaries. Host-Build-Abhängigkeiten bleiben ein expliziter Operator-Schritt, damit keine unkontrollierten Paket- oder Systemänderungen im Hintergrund passieren.
