# HW-TEST-1 Hardware-Testmatrix

Status: **vorbereitet, nicht ausgefuehrt**  
Quelle: `data/diagnostics/hw_test_1_matrix.json`

## Matrix-Spalten (verbindlich)

- Test-ID
- Plattform
- Quellzustand
- Zielmedium
- Dateisystem Zielmedium
- Verschluesselung an/aus
- Key-Datei Status
- Testart
- Erwartetes Ergebnis
- Evidence-Pflicht
- moegliche Diagnose-IDs
- Ergebnis (`planned`, `passed`, `failed`, `inconclusive`)

## Abdeckung

- A: Laptop interne NVMe -> externe NVMe (`HW1-01` bis `HW1-05`)
- B: Laptop interne NVMe -> USB-3.2-Stick 64 GB (`HW1-06` bis `HW1-10`)
- C: Laptop interne NVMe -> SD-Karte 64 GB (`HW1-11` bis `HW1-15`)
- D: Negativ-/Grenzfaelle (`HW1-16` bis `HW1-24`)

## Hinweis zur Auswertung

- `planned` bedeutet: Testfall ist definiert, aber noch nicht real ausgefuehrt.
- `passed` darf nur gesetzt werden, wenn der definierte Zielzustand inkl. Nachweisen erreicht ist.
- Preview-/Sandbox-Erfolg gilt nicht automatisch als echter Recovery-Erfolg.
