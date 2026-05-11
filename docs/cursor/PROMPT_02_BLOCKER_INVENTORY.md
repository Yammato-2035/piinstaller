# Prompt 2 – Blocker-Inventar (Master-Spezifikation)

> **Hinweis Dateinamen:** `PROMPT_02_HARDWARE_TEST_MATRIX.md` betrifft nur die Hardware-Matrix-Vorbereitung. **Dieses Dokument** entspricht „Prompt 2 – Aktuelle Probleme gezielt erfassen“ aus der Produktionsreife-Spezifikation.

```text
STRICT MODE – SETUPHELFER BLOCKER INVENTORY

ZIEL:
Erfasse alle bestehenden Probleme, die Produktionsreife, Hardwaretests, Backup/Restore, Bootstick oder Website-Transparenz blockieren.

NICHT ERLAUBT:
- keine Feature-Implementierung
- keine Refactorings
- keine Löschoperationen
- keine echten Restores
- keine Systempfade verändern

PHASE 1 – TESTBESTAND ERFASSEN
- finde vorhandene Tests
- finde Testdokumentation
- finde Evidence-Dateien
- finde bekannte Abschlussberichte

PHASE 2 – FEHLER ERFASSEN
- fehlschlagende Tests
- fehlende Tests
- unstabile Bereiche
- Legacy-Namen pi-installer/setuphelfer
- Service-/Port-Konflikte
- Pfad-/Mount-/Permission-Probleme

PHASE 3 – BLOCKER KLASSIFIZIEREN
- P0: blockiert Backup/Restore/Hardwaretest
- P1: blockiert Rescue/Release
- P2: blockiert Website/Transparenz
- P3: später

PHASE 4 – OUTPUT
Aktualisiere:
- docs/roadmap/STATUS_MATRIX.md
- docs/evidence/release-gates/current_failures.json
- docs/evidence/release-gates/runtime_inventory.json

ABSCHLUSSBERICHT:
1. P0-Blocker
2. P1-Blocker
3. P2-Blocker
4. P3-Punkte
5. empfohlene Reihenfolge
```

## Evidence-Ausgabe dieser Ausführung

- Maschinenlesbar: `docs/evidence/release-gates/blocker_inventory.json`
- Kurzbericht: `docs/evidence/release-gates/prompt02_abschlussbericht.md`
