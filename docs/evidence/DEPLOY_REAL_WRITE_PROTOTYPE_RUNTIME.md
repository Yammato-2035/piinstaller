# Evidence: DEPLOY_REAL_WRITE_PROTOTYPE runtime

## Datum

2026-05-08 (Agent-Lauf, Entwicklungsrechner).

## Automatisierte Tests

- Befehl: `python3 -m unittest tests.test_deploy_real_write_prototype_v1 -v` (Arbeitsverzeichnis: `backend/`)
- Ergebnis: **OK** (12 Tests, 1 übersprungen wenn `fastapi` fehlt: Routen-Registrierung)
- Abgedeckt u. a.: fehlendes Feature-Flag, Image >512MB (gemockt), Mount-Recheck, Readonly-Recheck, Fingerprint-Mismatch, fehlender Harness, kein Blockdevice, Verify-Mismatch (gemockt), erfolgreicher Write auf Datei mit Blockdevice-Mock, Verbot von `subprocess`/`os.system` im Modulquelltext

## E2E auf physischem USB/SD

- **Nicht ausgeführt** in dieser Umgebung: kein entbehrliches Testmedium angeschlossen; keine manuellen `lsblk`/`findmnt`-Vorher/Nachher-Protokolle.
- Vorgehen für manuelle Nachverfolgung (nur wenn Medium entbehrlich ist):
  1. Kleines Image (≤512MB, z. B. 8MB) im erlaubten Cache-Pfad erzeugen, Checksumme ermitteln.
  2. Vollständige Gate-Kette inkl. Harness und Real-Write-Check wie in der API-Doku.
  3. `SETUPHELFER_ENABLE_REAL_WRITE=1` setzen.
  4. `POST /api/deploy/write/prototype` aufrufen.
  5. Vorher/Nachher: `lsblk`, `findmnt`, `mount` — sicherstellen, dass das Ziel ungemountet blieb und keine internen Systemplatten betroffen sind.

## Interne Laufwerke

- Kein Laufzeitnachweis auf diesem Host; die Implementierung blockiert nicht-removable/ungesicherte Ziele über `validate_test_device` + Safety.

## Abnahme-Hinweis

- **Code + Unit-Tests:** lauffähig geprüft.
- **Hardware-E2E:** ausstehend / freiwillig nur mit Wegwerfmedium.
