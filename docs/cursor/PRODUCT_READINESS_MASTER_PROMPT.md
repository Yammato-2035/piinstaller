# Master Prompt – Setuphelfer Produktionsreife

```text
STRICT MODE – SETUPHELFER PRODUKTIONSREIFE OHNE NEUE FEATURES

ZIEL:
Bringe das Projekt Setuphelfer in Richtung Produktions- und Monetarisierungsreife, ohne neue Features zu entwickeln.

AKTIVE ZIELE:
1. Statusmatrix anlegen/aktualisieren
2. Testmatrizen anlegen/aktualisieren
3. bestehende Fehler erfassen
4. Backup/Restore/Verify validieren
5. Hardwaretests vorbereiten
6. Rescue-Stick read-only vorbereiten
7. Monolith nur analysieren, nicht refactoren
8. Website-/Affiliate-Transparenz vorbereiten
9. Release-Gates definieren

NICHT ERLAUBT:
- keine Cloudserver Edition implementieren
- kein Plesk-Modul
- kein Modulshop
- keine neuen Premium-Funktionen
- keine großen UI-Redesigns
- keine neuen Produktideen
- kein echter Restore ohne ausdrückliches Hardwaretest-Runbook
- keine Schreiboperationen auf interne Laufwerke
- kein sudo ohne explizite Freigabe
- keine Secrets committen

PHASE 0 – IST-STAND
- Prüfe vorhandene Roadmap-, Testing-, Evidence- und Cursor-Dateien.
- Erstelle eine Liste fehlender Dateien.
- Ändere noch keinen Produktcode.

PHASE 1 – DATEIEN ANLEGEN
Lege an, falls fehlend:
- docs/roadmap/STATUS_MATRIX.md
- docs/roadmap/ROADMAP_2026.md
- docs/roadmap/RELEASE_READINESS_CHECKLIST.md
- docs/roadmap/MONETIZATION_READINESS_CHECKLIST.md
- docs/roadmap/PUBLIC_STATUS_PAGE.md
- docs/testing/HARDWARE_TEST_MATRIX.md
- docs/testing/BACKUP_RESTORE_TEST_MATRIX.md
- docs/testing/RESCUE_STICK_TEST_MATRIX.md
- docs/testing/WEBSITE_TRANSPARENCY_TEST_MATRIX.md
- docs/testing/AFFILIATE_TRANSPARENCY_TEST_MATRIX.md
- docs/evidence/README.md

PHASE 2 – AMPELSTATUS
Setze für jeden Bereich Startstatus:
- Grün nur bei vorhandener Evidence
- Gelb bei teilweiser Umsetzung
- Rot bei offen/geplant
- Schwarz bei bewusst geparkt

PHASE 3 – KEINE FEATURES
Falls Codeänderungen erforderlich scheinen:
- nur dokumentieren
- nicht umsetzen
- als Issue/ToDo erfassen

PHASE 4 – ABSCHLUSSBERICHT
Berichte:
1. angelegte Dateien
2. nicht angelegte Dateien
3. erkannte Blocker
4. Ampelstatus
5. nächste 10 priorisierte Aufgaben
6. keine neuen Features bestätigt
```

## Zugehörige Prompt-Dateien

- **Blocker-Inventar** (Spezifikation „Prompt 2“): [`PROMPT_02_BLOCKER_INVENTORY.md`](./PROMPT_02_BLOCKER_INVENTORY.md) → Evidence: `docs/evidence/release-gates/blocker_inventory.json`
