# FAQ: Hardwareondersteuning (NL)

Korte antwoorden over de nieuwe hardwaredetectie- en provisioneringslaag
(PI-RS-HW-COMPAT-PROVISION-001). Geen marketingtaal.

Talen: [Deutsch](HARDWARE_SUPPORT_FAQ_DE.md) · [English](HARDWARE_SUPPORT_FAQ_EN.md) · [Français](HARDWARE_SUPPORT_FAQ_FR.md) · [Nederlands](HARDWARE_SUPPORT_FAQ_NL.md)

## Ondersteunt Setuphelfer mijn grafische kaart?

De GPU wordt gedetecteerd en zijn status (gebonden stuurprogramma, geladen
module, firmware, DRM-apparaat, actieve bootparameters zoals `nomodeset`)
apart beoordeeld. Of de weergave echt werkt, kan alleen een fysieke test
bevestigen — zie
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.

## Installeert de reddingsstick automatisch NVIDIA-/proprietaire stuurprogramma's?

Nee. Proprietaire stuurprogramma's worden alleen getoond als **duidelijk
gelabelde optie** (`driver_type: proprietary_optional`). Ze worden nooit
automatisch geïnstalleerd.

## Wat betekent „review_required" voor de chipset?

De chipset wordt alleen benoemd als PCI-ID, DMI-gegevens of een gecureerd
catalogusitem een betrouwbare match toelaten. Bij onvoldoende data meldt het
systeem eerlijk `review_required` in plaats van een geraden naam.

## Kan ik mijn printer/scanner meteen gebruiken?

De reddingsstick toont of een passend stuurprogramma/backend bekend is en
biedt een stuurprogrammaplan. Een echte testprint/scan wordt **niet**
automatisch gestart — dat blijft een bewuste operatoractie buiten deze fase.

## Ondersteunt Setuphelfer alle Raspberry Pi-modellen gelijk?

Nee. Raspberry Pi 3, 3B+, 4, 400, CM4, Pi 5 en CM5 worden individueel via
device-tree gedetecteerd en krijgen elk eigen bootmedium- en
OS-compatibiliteitsbeoordelingen. Details:
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_NL.md`.

## Waarom bevat de 64-GB-stick niet gewoon alle besturingssystemen?

Omdat de ruimte beperkt is. Setuphelfer gebruikt een imagecatalogus met
ondertekende bronnen, checksums en een begrensde cache in plaats van een
starre „alles-erbij"-image. Details:
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_NL.md`.

## Installeert deze versie al besturingssystemen?

Nee. `write_allowed` is in deze fase voor elk provisioneringsplan altijd
`false`. Er vindt geen schrijfactie plaats op echte opslagmedia.

## Welke gegevens worden naar de cloud gestuurd?

Alleen een geredigeerde samenvatting (platformklasse, CPU-/GPU-fabrikant,
apparaattellingen per status, kernelversie, rescue-payloadversie,
issue-codes). Serienummers, MAC-/IP-adressen en volledige EDID-gegevens
worden nooit verzonden.
