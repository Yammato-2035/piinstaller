# HW-TEST-1 Pi-Freigabekriterien

Der isolierte Raspberry-Pi-Test ist erst freigegeben, wenn alle Kriterien erfuellt sind.

## Muss-Kriterien

1. externe NVMe erfolgreich getestet.
2. USB-Stick erfolgreich getestet.
3. SD-Karte erfolgreich getestet.
4. mindestens ein verschluesselter und ein unverschluesselter Pfad erfolgreich.
5. Verify/Manifest/Hash/Path-Containment-Grenzfaelle plausibel abgedeckt.
6. Rechte-/Gruppenmodell auf Wechselmedien verifiziert.
7. neue EvidenceRecords sauber abgelegt.
8. keine unbekannte kritische Root-Cause offen.

## Sperrkriterien (keine Pi-Freigabe)

- Ein Muss-Kriterium nicht erfuellt.
- Kritische Befunde ohne bestaetigten Workaround.
- Nur Preview-/Sandbox-Erfolge vorhanden, aber kein belastbarer Endzustand.

## Freigabeentscheidung

- `pi_release_status = blocked | conditional | approved`
- Standard in dieser Phase: **blocked**, bis Matrix-Tests real durchgefuehrt und evidenzbasiert abgeschlossen sind.
