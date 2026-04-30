# FAQ – Backup & Restore – Deutsch

## Warum darf das Backup nicht auf dem Root-Dateisystem liegen?

Ein Backup auf dem gleichen Dateisystem wie das laufende System ist unsicher. Bei einem Festplattenfehler, einer Fehlbedienung oder einem Restore-Fehler kann das Backup gleichzeitig mit dem Original verloren gehen.

## Warum wurde `/mnt/setuphelfer/backups` blockiert?

Der Pfad lag auf dem Root-Dateisystem und war kein eigenes sicheres Zielmedium. Die Storage-Schutzlogik hat deshalb korrekt blockiert.

## Warum war `/media/...` zunächst blockiert?

Die frühere Logik blockierte `/media` pauschal. Das war zu streng, weil Linux-Desktop-Systeme externe Datenträger typischerweise unter `/media/<user>/...` einhängen.

## Wie wurde das korrigiert?

`/media` wird nicht pauschal freigegeben. Ein Ziel unter `/media` ist nur erlaubt, wenn es auf ein echtes, sicheres Blockgerät zeigt und nicht System-, Boot-, Windows- oder EFI-Partition ist.

## Warum muss `/media` beim Full-Backup ausgeschlossen werden?

Wenn `/` gesichert wird, würde `/media` sonst externe Datenträger mit in das Backup aufnehmen. Das kann zu riesigen Backups, rekursiven Läufen oder Stalls führen.

## Welche Pfade sind bei Full-Backup ausgeschlossen?

Mindestens:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- `/media`
- `/run/media`
- konkreter Backup-Zielpfad

## Warum blieb das Backup hängen?

Der konkrete Lauf blieb bei ca. 27,46 GB stehen. Wahrscheinliche Ursachen waren:

- zu breiter Quellumfang inklusive `/media`
- mögliches Pipe-Blocking durch tar stdout/stderr

## Was wurde geändert?

- `/media` und `/run/media` wurden als Excludes ergänzt.
- stdout wird nicht mehr gepuffert.
- stderr wird während des Laufs konsumiert.

## Was ist nach dem Fix noch zu tun?

Ein neuer Full-Backup-Lauf muss erfolgreich abgeschlossen werden. Danach müssen Manifest, Basic Verify und möglichst Deep Verify geprüft werden.

## Wann ist Monolith-Refactoring erlaubt?

Erst wenn:

- Target-Check erfolgreich ist
- Full Backup erfolgreich ist
- Manifest vorhanden ist
- Verify erfolgreich ist
