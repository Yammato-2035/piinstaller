# Rescue-Stick: Peripherie-Erkennung und Treiber-Katalog

**Stand:** 2026-08-02

## Was das ist

`backend/core/rescue_peripheral_discovery.py` erweitert die Rescue-Assessment-Ausgabe
(`system-assessment.v2`, siehe `backend/core/rescue_system_assessment_v2.py`) um eine
`peripherals`-Sektion: USB-Geräte (`lsusb`, keyword-klassifiziert nach
Tastatur/Maus/Webcam/Audio/Drucker/Storage/KI-Beschleuniger), Eingabegeräte
(`/proc/bus/input/devices`) und Audiokarten (`aplay -l`). Read-only, nach demselben
Muster wie der Rest von `rescue_system_assessment_v2.py`: fehlendes Tool → Eintrag in
`missing_tools`, nie ein Absturz.

`backend/core/driver_catalog.py` ist eine kleine Vendor-Keyword → offizielle
Hersteller-Support-URL-Tabelle. `derive_driver_hints()` in
`rescue_system_assessment_v2.py` gleicht GPU-Treiberlücken (`gpu.vendor_driver_gaps`)
und erkannte Peripherie (Drucker/Webcam/Audio/KI-Beschleuniger) gegen den Katalog ab
und liefert `driver_hints: [{vendor, official_url, context}]` im Assessment-Output.

## Bewusste Grenzen

- **Keine Vollständigkeit.** Der Katalog enthält aktuell NVIDIA, AMD, Intel, Realtek,
  Broadcom, Qualcomm, Logitech, Corsair, Lenovo, Dell, HP, Canon, Epson, Brother — eine
  **lebende, erweiterbare Liste**, kein Anspruch auf alle Hersteller der letzten 20 Jahre.
  Neue Einträge: `backend/core/driver_catalog.py::DRIVER_CATALOG` ergänzen (Vendor,
  offizielle Support-Domain, Keywords, Kategorie).
- **Nur offizielle Hersteller-Domains.** Bisher gab es dafür keine Policy — diese Regel
  gilt ab jetzt für neue Katalogeinträge (kein Drittanbieter-/Affiliate-Link).
- **Plan-only.** `driver_hints` sind reine Informationslinks, keine Ausführung, kein
  automatischer Download/Install — passt zu `RecommendationMode.DOCUMENTATION` in
  `core/diagnostic_finding_contract.py`.
- **Keyword-Klassifikation, keine echte USB-Device-Class-Auswertung.** `lsusb`-Text wird
  nach Stichworten durchsucht (gleicher Ansatz wie `backend/app.py::peripherals_scan()`
  für die Hauptapp), nicht nach USB-Klassen-IDs. Fehlklassifikationen sind möglich.
- **Kein physischer Mehrgeräte-Nachweis.** Wie bei jeder neuen Hardware-Klasse in diesem
  Projekt gilt: kein Grün ohne dokumentierten Boot-/Erkennungs-Befund auf echtem Gerät
  (siehe `docs/evidence/rescue/RESCUE_STICK_CAPABILITY_MATRIX.yaml`).

## Verwandt

- `frontend/src/pages/PeripheryScan.tsx` — die ältere, rein clientseitige
  `MANUFACTURER_DRIVER_LINKS`-Liste für die Hauptapp; sollte künftig auf
  `driver_catalog.py` als einzige Quelle umgestellt werden statt eine zweite Liste zu
  pflegen.
- `docs/roadmap/RESCUE_HARDWARE_ASSESSMENT_ROADMAP.md`
