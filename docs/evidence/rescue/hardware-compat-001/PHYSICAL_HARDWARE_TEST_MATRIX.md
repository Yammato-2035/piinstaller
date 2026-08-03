# Physische Hardware-Testmatrix — PI-RS-HW-COMPAT-PROVISION-001

**Phase:** 18 — Physische Testmatrix vorbereiten
**Status:** `planned` (keine physische Ausführung in dieser Phase)
**Maschinenlesbare Fassung:** `physical_hardware_test_matrix.json`

## Zweck

Diese Matrix listet die für PI-RS-HW-COMPAT-PROVISION-001 relevanten physischen
Testfälle auf. Sie ist **keine** Behauptung über tatsächlich verifizierte
Hardware. Alle in dieser Phase erstellten Module (Phase 2–16) wurden ausschließlich
gegen **synthetische Fixtures** (injizierte `raw_text`, `sysfs_root`, `runner`)
getestet — siehe `backend/tests/test_*_v1.py`. Ein grüner Unit-Test ist **kein**
Ersatz für `physically_verified`.

## Statuswerte

| Status | Bedeutung |
|---|---|
| `planned` | Testfall identifiziert, noch nicht ausgeführt |
| `detected` | Gerät wurde bei einem realen Lauf erkannt |
| `driver_plan_created` | Treiberplan wurde für ein reales Gerät erzeugt (keine Installation) |
| `physically_verified` | Funktion wurde am realen Gerät durch einen Operator bestätigt |
| `limited` | Funktion nur eingeschränkt nutzbar |
| `blocked` | Sichere Aktivierung/Nutzung nicht möglich |
| `unavailable` | Kein Testgerät für diese Spalte vorhanden/zutreffend |

## Matrix

| Plattform | CPU | GPU | Mainboard | USB | Drucker | Scanner | Netzwerk | Boot | Status |
|---|---|---|---|---|---|---|---|---|---|
| MSI GE63 Raider RGB 8RF (MS-16P5) | planned | planned | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| ASUS ROG Strix G513QM | planned | planned | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| Intel-Desktop/-Notebook (generisch) | planned | planned | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| AMD-Desktop/-Notebook (generisch) | planned | planned | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| Raspberry Pi 3 / 3B+ | planned | unavailable | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| Raspberry Pi 4 / 400 / CM4 | planned | unavailable | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| Raspberry Pi 5 / CM5 | planned | unavailable | planned | planned | unavailable | unavailable | planned | planned | **planned** |
| Tintenstrahldrucker (generisch) | unavailable | unavailable | unavailable | planned | planned | unavailable | planned | unavailable | **planned** |
| Monochrom-Laserdrucker (generisch) | unavailable | unavailable | unavailable | planned | planned | unavailable | planned | unavailable | **planned** |
| Farblaserdrucker/Farb-MFP (generisch) | unavailable | unavailable | unavailable | planned | planned | planned | planned | unavailable | **planned** |
| Netzwerkdrucker (generisch, falls vorhanden) | unavailable | unavailable | unavailable | unavailable | planned | unavailable | planned | unavailable | **unavailable** |
| Scanner (USB und/oder Netzwerk) | unavailable | unavailable | unavailable | planned | unavailable | planned | planned | unavailable | **planned** |
| USB-Tastatur und -Maus | unavailable | unavailable | unavailable | planned | unavailable | unavailable | unavailable | unavailable | **planned** |
| USB-Massenspeicher Nr. 1 | unavailable | unavailable | unavailable | planned | unavailable | unavailable | unavailable | planned | **planned** |
| USB-Massenspeicher Nr. 2 | unavailable | unavailable | unavailable | planned | unavailable | unavailable | unavailable | planned | **planned** |

## Wichtige Hinweise

- **MSI GE63 / ASUS G513QM:** Für beide Geräte existiert bereits *ältere* Boot-/Firmware-Evidenz
  aus früheren Rescue-Stick-Phasen (siehe `data/hardware/hardware_compat_catalog.json`).
  Diese ältere Evidenz wurde **nicht verändert** und bleibt gültig. Sie deckt jedoch
  nicht die in dieser Phase neu geschaffenen Module (CPU-/GPU-/Mainboard-Detection,
  Driver-Resolver usw.) ab — dafür ist ein neuer physischer Testlauf erforderlich.
- **Raspberry Pi 3/4/5:** Kein Zugriff auf reale Boards in dieser Entwicklungsphase.
  Die Module `platforms/raspberry_pi_*.py` sind rein gegen Device-Tree-Textfixtures
  verifiziert.
- **Drucker/Scanner:** Kein reales Gerät in dieser Phase angeschlossen. Technologie-
  und Farbklassifikation bleiben laut Spezifikation `unknown`/`review_required`,
  bis IPP-/PPD-Daten eines realen Geräts vorliegen.
- **Netzwerkdrucker:** Kein konkretes Gerät benannt — Zeile bleibt als Platzhalter
  `unavailable`, bis ein Testgerät zur Verfügung steht.
- Kein Eintrag dieser Matrix darf ohne echten Operator-Testlauf auf
  `physically_verified` gesetzt werden.

## Nächster Schritt

Sobald reale Testgeräte verfügbar sind: pro Zeile einen Lauf gegen
`GET /api/rescue/hardware/*` (Phase 14) durchführen, Ergebnis in
`physical_hardware_test_matrix.json` aktualisieren und Status begründet auf
`detected` / `driver_plan_created` / `physically_verified` / `limited` / `blocked`
setzen.
