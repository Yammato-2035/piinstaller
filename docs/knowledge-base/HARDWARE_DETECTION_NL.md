# Kennisbank: Hardwaredetectie op de reddingsstick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16). Doelgroep: gebruikers en support.

Talen: [Deutsch](HARDWARE_DETECTION_DE.md) · [English](HARDWARE_DETECTION_EN.md) · [Français](HARDWARE_DETECTION_FR.md) · [Nederlands](HARDWARE_DETECTION_NL.md)

## Wat doet de reddingsstick met mijn hardware?

Hij herkent apparaten read-only via bestaande Linux-mechanismen (sysfs,
PCI-/USB-ID's, kernel-modalias) en beoordeelt hun bedrijfsstatus in meerdere
stappen: gedetecteerd → stuurprogramma bekend → aanwezig → module geladen →
firmware aanwezig → gereed. Hij brengt **geen** wijzigingen aan in uw systeem.

## Betekent „gedetecteerd" dat het apparaat werkt?

**Nee.** Detectie is de eerste stap, geen functioneringsgarantie. Een apparaat
kan gedetecteerd zijn maar geblokkeerd zonder passend kernelmodule, zonder
firmware of door een bootparameter.

## Wat tonen de verkeerslichten?

- 🟢 Groen: gedetecteerd, stuurprogramma geladen, firmware aanwezig, gereed
- 🟡 Geel: beperkt bruikbaar, optioneel stuurprogramma, fysieke test nodig
- 🔴 Rood: stuurprogramma/firmware ontbreekt, kernel incompatibel, geblokkeerd
- ⚪ Grijs: onbekend, niet gecontroleerd, tool ontbreekt

## Wat is een „stuurprogrammaplan"?

Een stuurprogrammaplan is een **voorstel** welk stuurprogramma/pakket zou
passen — inclusief bronvertrouwen, licentiehints en Secure Boot-impact. Het is
**geen** installatie.

## Waarom worden printers/scanners niet altijd eenduidig geclassificeerd?

Printtechnologie en kleurcapaciteit worden alleen uit belastbare bronnen
afgeleid (IPP-capaciteiten, CUPS-/PPD-metagegevens, gecureerde catalogus) —
nooit uit een geraden modelnaam. Bij onduidelijke data: `unknown`/`review_required`.

## Wat gebeurt er bij een multifunctioneel apparaat?

Printer-, scanner- en eventuele andere functies van hetzelfde apparaat worden
**apart** beoordeeld.

## Wordt Raspberry Pi 3–5 volledig ondersteund?

Er is geen algemene uitspraak. Elke combinatie van board, architectuur, OS en
bootmedium wordt apart beoordeeld. Details:
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_NL.md`.

## Waarom past niet elk OS-image op de 64-GB-stick?

Een 64-GB-stick kan niet onbeperkt volledige images bevatten. Setuphelfer
gebruikt een catalogus van ondertekende images en een begrensde cache. Details:
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_NL.md`.
