# Backup/Recovery File-Engine – Realitätscheck

## Ausgangslage (reales Problem)

- `create_file_backup` hat bisher nur reguläre Dateien aufgenommen.
- Bei `tf.add(..., arcname=p.name)` wurden Pfade abgeflacht.
- Folgen:
  - Verzeichnisse wie `/etc`, `/home`, `/opt` wurden nicht rekursiv gesichert.
  - Namenskollisionen waren möglich.
  - Restore-/Verify-Aussagen konnten ein Full-Recovery falsch positiv wirken lassen.

## Umgesetzte Korrektur

- Rekursive Verzeichnisarchivierung für file-basiertes Backup.
- Relative Archivpfade ohne führenden Slash (`etc/hosts`, `home/...`, `opt/...`).
- Kollisionserkennung für Archivzielpfade mit sauberem Fehlerabbruch.
- Überlappende Eingaben werden dedupliziert (z. B. `/home` plus `/home/user`), dokumentiert im Manifest (`skipped_inputs`).
- Restriktives Verhalten bei Symlinks/Sonderdateien: Abbruch statt stiller Teil-Sicherung.

## Verify-/Restore-Konsistenz

- Verify prüft unsichere Member (Traversal, absolute Pfade, Links/Sondertypen) vor Verarbeitung.
- Deep-Verify bewertet Manifestpfade gegen die extrahierte relative Struktur.
- Restore entpackt nur sichere Member und verhindert Zielpfad-Ausbruch aus dem erlaubten Ziel.

## Grenzen (weiterhin offen)

- Kein Boot-Nachweis durch Unit-Tests.
- Kein vollständiger End-to-End-Lauf (Backup -> Restore -> Reboot) allein durch diese Änderung bewiesen.
- Raspberry-Pi-Bootpfad bleibt separat auf Hardware zu prüfen.

## Empfohlene Testreihenfolge

1. Unit-Tests + `py_compile` lokal.
2. End-to-End in VM: Backup erstellen, Restore durchführen, System rebooten, Boot/Services prüfen.
3. Danach Hardwarelauf auf Raspberry Pi mit identischer Prüflogik.

## Warnung für Betrieb

Ein „Backup erfolgreich“ ohne erfolgreichen Boot-Nachweis nach Restore ist kein belastbarer Full-Recovery-Beweis.
