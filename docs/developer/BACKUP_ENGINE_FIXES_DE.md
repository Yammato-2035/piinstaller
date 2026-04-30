# Backup Engine Fixes – Deutsch

## Ziel

Dokumentation der Korrekturen am Full-Backup-Verhalten nach einem reproduzierbaren Stall während eines Realhardware-Tests.

## Ausgangslage

Ein Full-Backup wurde auf ein externes Zielmedium gestartet:

- Zielpfad: `/media/volker/setuphelfer-back/backups`
- Zielgerät: `/dev/sda1`
- Dateisystem: ext4
- Rechte: `root:setuphelfer`, `2770`

Der Job lief zunächst an, blieb dann aber bei ca. 27,46 GB stehen.

## Ursache 1: Zu breiter Backup-Quellumfang

Die Full-Backup-Logik nutzte `/` als Quelle.

Bereits ausgeschlossen waren:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- konkreter `backup_dir`

Nicht ausgeschlossen waren:

- `/media`
- `/run/media`

Dadurch wurden externe Datenträger unter `/media` in den Backup-Scope aufgenommen.

Risiken:

- Mitbackup externer Medien
- Mitbackup fremder Datenpartitionen
- Mitbackup des Backup-Zielmediums außerhalb des konkreten Zielordners
- sehr große oder rekursive Backup-Läufe
- Stall oder unklare Laufzeit

## Fix 1: Zusätzliche Excludes

Für Full-Backups wurden ergänzt:

```text
--exclude=/media
--exclude=/run/media
```

Damit bleiben Desktop-Automounts und externe Medien außerhalb des Root-Full-Backups.

## Ursache 2: Mögliches Pipe-Blocking

Die cancelbare tar-Ausführung verwendete stdout/stderr als PIPE und las diese erst nach Prozessende aus.

Risiko:

Wenn tar viele Warnungen oder Fehlermeldungen schreibt, kann der Pipe-Puffer volllaufen.
Der Prozess blockiert dann, obwohl kein Python-Fehler auftritt.

## Fix 2: Robusteres Subprozess-Handling

Um Pipe-Backpressure zu vermeiden:

- stdout wird auf DEVNULL geleitet.
- stderr wird während des Laufs kontinuierlich konsumiert.
- Cancel-Logik und Rückgabecode-Auswertung bleiben erhalten.

## Sicherheitsbewertung

Die Storage-Schutzlogik wurde nicht abgeschwächt.

Weiterhin verboten:

- Backup auf Root-FS
- Backup auf Systemdisk
- Backup auf Windows-/EFI-Partition
- unsichere Pfade ohne echtes Blockdevice

Erlaubt ist `/media` nur als Ziel, wenn die bestehende Zielvalidierung ein echtes, sicheres externes Blockgerät erkennt.

## Tests

Ergänzte/ausgeführte Tests:

- Full-Backup enthält `/media` und `/run/media` als Excludes.
- Bestehende Excludes bleiben erhalten.
- Backup-Zielpfad wird weiter ausgeschlossen.
- cancelbare tar-Ausführung nutzt kein blockierendes stdout-PIPE.
- Storage-Protection-Tests bleiben erfolgreich.

## Offener Punkt

Nach dem Fix muss ein erneuter Full-Backup-Lauf mit anschließendem Verify durchgeführt und dokumentiert werden.
