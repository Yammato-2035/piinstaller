# BR-001: Live-Cache / tar exit 1 auf aktiven Desktops

## Symptom

- `backup.failed`, `tar_failed`, `TAR_CRITICAL_WARNING`
- stderr: `Datei hat sich beim Lesen geändert` (z. B. Chrome `Cache_Data`)
- Großes Partial, kein `.tar.gz`, kein SHA256, kein Verify Deep

## Ursache

- Browser- und Desktop-Caches sind während des Laufs schreibaktiv.
- **Timeshift** (`/timeshift`, `/timeshift/snapshots`): Live-Snapshots ändern sich beim Lesen → `Datei hat sich beim Lesen geändert`, `TAR_CRITICAL_WARNING`, `tar_failed`.
- `full-expert` sichert `/` inkl. dieser Pfade (bitgenau/maximal, nicht stabil für BR-001).

## Empfehlung für nächsten BR-001-Retry

1. Profil **`full-root-stable`**: Full-Root mit dokumentierten Excludes für **Timeshift**, `~/.cache`, Chrome/Chromium-Caches, Trash — stabilitätsorientiert, kein Raw-Full-System-Bitgenauigkeit.
2. Alternativ: Browser schließen, Timeshift pausieren, weiter `full-expert` (risikoreicher).
3. Package-Freeze aktiv lassen; Partial vor Retry separat bereinigen.

## Timeshift (Job 6d4e161b2f8c, 2026-05-20)

- pigz lief korrekt; Abbruch durch `/timeshift`-Live-Änderungen, nicht durch Kompression.
- Ab Fix: `full-root-stable` setzt `--exclude=/timeshift` (und Unterpfade) auf dem tar-Befehl; `full-expert` unverändert.

## Abgrenzung

- Kein Restore ohne finales Archiv und Verify Deep.
- Exit 1 niemals als BR-001 grün werten.

## Referenz-Lauf

- Job `2a15912d1b52` (2026-05-20): ~3h57, ~227 GiB, Chrome-Cache live file.
