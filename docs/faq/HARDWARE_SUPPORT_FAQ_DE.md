# FAQ: Hardware-Unterstützung (DE)

Kurzantworten zur neuen Hardware-Erkennungs- und Provisionierungsschicht
(PI-RS-HW-COMPAT-PROVISION-001). Keine Produktwerbung.
Sprachen: [Deutsch](HARDWARE_SUPPORT_FAQ_DE.md) · [English](HARDWARE_SUPPORT_FAQ_EN.md) · [Français](HARDWARE_SUPPORT_FAQ_FR.md) · [Nederlands](HARDWARE_SUPPORT_FAQ_NL.md)

## Unterstützt Setuphelfer meine Grafikkarte?

Die GPU wird erkannt und ihr Zustand (Treiber gebunden, Modul geladen,
Firmware, DRM-Gerät, aktiver Bootparameter wie `nomodeset`) getrennt
bewertet. Ob die Displayausgabe tatsächlich funktioniert, kann nur ein
physischer Test bestätigen — siehe
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.

## Installiert der Rettungsstick automatisch NVIDIA-/proprietäre Treiber?

Nein. Proprietäre Treiber werden nur als **gekennzeichnete Option**
angezeigt (`driver_type: proprietary_optional`). Eine Installation erfolgt
nie automatisch.

## Was bedeutet „review_required" beim Chipsatz?

Der Chipsatz wird nur benannt, wenn PCI-ID, DMI-Daten oder ein kuratierter
Katalogeintrag eine belastbare Zuordnung erlauben. Reicht die Datenlage
nicht aus, wird ehrlich `review_required` statt einer geratenen Bezeichnung
angezeigt.

## Kann ich meinen Drucker/Scanner sofort nutzen?

Der Rettungsstick zeigt an, ob ein passender Treiber/Backend bekannt ist
und einen Treiberplan. Ein tatsächlicher Testdruck/Testscan wird **nicht**
automatisch ausgeführt — das bleibt eine bewusste Operatoraktion außerhalb
dieser Phase.

## Unterstützt Setuphelfer alle Raspberry-Pi-Modelle gleich?

Nein. Raspberry Pi 3, 3B+, 4, 400, CM4, Pi 5 und CM5 werden einzeln über
Device-Tree-Daten erkannt und erhalten jeweils eigene Bootmedium- und
OS-Kompatibilitätsbewertungen. Details:
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_DE.md`.

## Warum enthält der 64-GB-Stick nicht einfach alle Betriebssysteme?

Weil der Platz begrenzt ist. Setuphelfer nutzt einen Imagekatalog mit
signierten Quellen, Prüfsummen und einem begrenzten Cache statt eines
starren „Alles-drauf"-Images. Details:
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_DE.md`.

## Werden mit dieser Version schon Betriebssysteme installiert?

Nein. `write_allowed` ist in dieser Phase für jeden Provisionierungsplan
immer `false`. Es findet kein Schreibvorgang auf reale Datenträger statt.

## Welche Daten werden zur Cloud übertragen?

Nur eine redigierte Zusammenfassung (Plattformklasse, CPU-/GPU-Hersteller,
Anzahl Geräte je Status, Kernelversion, Rescue-Payload-Version,
Issue-Codes). Seriennummern, MAC-/IP-Adressen und vollständige EDID-Daten
werden nie übertragen.
