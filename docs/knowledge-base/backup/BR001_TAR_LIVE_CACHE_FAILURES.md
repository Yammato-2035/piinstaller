# BR-001: Live-Cache / tar exit 1 auf aktiven Desktops

## Symptom

- `backup.failed`, `tar_failed`, `TAR_CRITICAL_WARNING`
- stderr: `Datei hat sich beim Lesen geändert` (z. B. Chrome `Cache_Data`)
- Großes Partial, kein `.tar.gz`, kein SHA256, kein Verify Deep

## Ursache

Browser- und Desktop-Caches sind während des Laufs schreibaktiv. `full-expert` sichert `/` inkl. dieser Pfade.

## Empfehlung für nächsten BR-001-Retry

1. Profil **`full-root-stable`**: Full-Root mit dokumentierten Excludes für `~/.cache`, Chrome/Chromium-Caches, Trash — keine heimlichen Datenlöschungen außerhalb dieser Kategorien.
2. Alternativ: Browser schließen, weiter `full-expert` (risikoreicher).
3. Package-Freeze aktiv lassen; Partial (~212 GiB) vor Retry separat bereinigen.

## Abgrenzung

- Kein Restore ohne finales Archiv und Verify Deep.
- Exit 1 niemals als BR-001 grün werten.

## Referenz-Lauf

- Job `2a15912d1b52` (2026-05-20): ~3h57, ~227 GiB, Chrome-Cache live file.
