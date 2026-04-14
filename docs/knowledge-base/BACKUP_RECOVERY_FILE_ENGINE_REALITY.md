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
- **Symlinks (2026-04):** In einer Debian-VM schlug ein Verzeichnis-Backup an `/etc` mit `Symlink source is not supported: /etc/alsa/conf.d/50-pipewire.conf` fehl. Ursache war die pauschale Ablehnung von Symlinks in `_collect_archive_members`. Behebung: Symlinks werden ohne Dereferenzierung archiviert; Manifest enthält `type: symlink` und `link_target`.
- **Sonderdateien:** werden nicht archiviert, erscheinen unter `skipped_members` (kein Totalausfall mehr).

## Verify-/Restore-Konsistenz

- Verify erlaubt symbolische Tar-Member; Hardlinks/FIFOs/Geräte bleiben blockiert.
- Deep-Verify prüft Symlinks per Manifest (`link_target`) und vermeidet `Path.resolve()` auf Symlink-Leafs.
- Restore erlaubt Symlinks mit Prüfung relativer Ziele gegen Pfadflucht (`backup_symlink_safety.py`); `extractall` nutzt `filter="tar"` wenn verfügbar.

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
