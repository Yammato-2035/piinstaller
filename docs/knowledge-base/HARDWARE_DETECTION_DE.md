# Wissensdatenbank: Hardwareerkennung im Rettungsstick

Stand: PI-RS-HW-COMPAT-PROVISION-001, Phase 19. Zielgruppe: Anwender und
Support. Kein Marketingtext.

## Was macht der Rettungsstick mit meiner Hardware?

Er erkennt Geräte lesend über bestehende Linux-Mechanismen (sysfs, PCI-/
USB-IDs, Kernel-Modalias) und bewertet ihren Betriebszustand in mehreren
Stufen: erkannt → Treiber bekannt → Treiber vorhanden → Modul geladen →
Firmware vorhanden → betriebsbereit. Er nimmt **keine** Änderungen an Ihrem
System vor.

## Bedeutet „erkannt", dass das Gerät funktioniert?

**Nein.** Erkennung ist der erste Schritt, keine Funktionsgarantie. Ein
Gerät kann erkannt sein, aber ohne passendes Kernelmodul, ohne Firmware
oder durch einen Bootparameter blockiert sein.

## Was zeigen die Ampeln an?

- 🟢 Grün: erkannt, Treiber geladen, Firmware vorhanden, betriebsbereit
- 🟡 Gelb: eingeschränkt nutzbar, optionaler Treiber, physischer Test nötig
- 🔴 Rot: Treiber/Firmware fehlt, Kernel inkompatibel, blockiert
- ⚪ Grau: unbekannt, nicht geprüft, Werkzeug fehlt

## Was ist ein „Treiberplan"?

Ein Treiberplan ist ein **Vorschlag**, welcher Treiber/welches Paket für ein
Gerät passen würde — inklusive Vertrauensstufe der Quelle, Lizenzhinweisen
und Secure-Boot-Auswirkung. Ein Treiberplan ist **keine Installation**. In
dieser Phase gibt es keine „Treiber installieren"-Schaltfläche, nur
„Treiberplan anzeigen".

## Warum werden Drucker/Scanner nicht immer eindeutig klassifiziert?

Drucktechnologie (Tintenstrahl/Laser/Matrix) und Farbfähigkeit werden nur
aus belastbaren Quellen (IPP-Fähigkeiten, CUPS-/PPD-Metadaten, kuratierter
Katalog) abgeleitet — nie aus einem geratenen Modellnamen. Ist die
Datenlage unklar, wird ehrlich `unbekannt`/`review_required` angezeigt.

## Was passiert bei einem Multifunktionsgerät?

Drucker-, Scanner- und ggf. weitere Funktionen desselben Geräts werden
**getrennt** bewertet. Eine funktionierende Druckfunktion sagt nichts über
die Scanfunktion aus.

## Wird Raspberry Pi 3–5 vollständig unterstützt?

Es gibt keine pauschale Aussage. Jede Kombination aus Board, Architektur,
Betriebssystem und Bootmedium wird einzeln bewertet. Details siehe
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT.md`.

## Warum passt nicht jedes Betriebssystem-Image auf den 64-GB-Stick?

Ein 64-GB-Stick kann nicht unbegrenzt vollständige Images enthalten.
Setuphelfer nutzt deshalb einen Katalog signierter Images, einen begrenzten
Cache und lädt Images bei Bedarf nach, statt alles vorzuinstallieren.
Details siehe `docs/rescue-stick/64GB_CARRIER_ARCHITECTURE.md`.

## Werden bei dieser Version schon echte Installationen durchgeführt?

**Nein.** Diese Phase liefert nur Erkennung, Klassifikation, Treiberpläne
und eine Installationsvorschau. Kein `dd`, kein `mkfs`, keine automatische
Installation. Reale, kontrollierte Schreibvorgänge folgen erst in einer
separaten, freigegebenen Folgephase.

## Werden meine Daten (Seriennummern, MAC-Adressen) übertragen?

Nein. Seriennummern, MAC-Adressen, IP-Adressen, vollständige EDID-Daten,
Benutzer-/Hostnamen und eindeutige Rohgerätekennungen sind von der
Telemetrie explizit ausgeschlossen (`backend/core/hardware_telemetry_contract.py`).
