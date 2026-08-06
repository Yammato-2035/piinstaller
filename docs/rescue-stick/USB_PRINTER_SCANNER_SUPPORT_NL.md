# USB-, printer- en scannerondersteuning — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Talen: [Deutsch](USB_PRINTER_SCANNER_SUPPORT_DE.md) · [English](USB_PRINTER_SCANNER_SUPPORT_EN.md) · [Français](USB_PRINTER_SCANNER_SUPPORT_FR.md) · [Nederlands](USB_PRINTER_SCANNER_SUPPORT_NL.md)

## USB-apparaatclassificatie (`backend/core/usb_device_detection.py`)

Gedetecteerde klassen (minimaal): massaopslag, HID, toetsenbord, muis,
printer, scanner, multifunctioneel apparaat, netwerkadapter, Wi-Fi,
Bluetooth, audio, camera, seriële adapters, smartcard, USB-hub,
externe GPU (alleen detectie), `unknown`.

Bronnen: USB-apparaatklasse, interfaceklassen, vendor/product-ID,
udev-eigenschappen, modalias, gebonden stuurprogramma, aanwezige
child-interfaces.

### Multifunctionele apparaten

Een samengesteld apparaat (bijv. printer+scanner+kaartlezer) wordt gemodelleerd
als **één apparaat met meerdere onafhankelijke capabilities**. Elke functie
krijgt een eigen `operational_status`. Setuphelfer beweert nooit dat een
functie gereed is alleen omdat een andere functie van hetzelfde apparaat is
gedetecteerd.

## Printers (`backend/peripherals/printer_detection.py`, `printer_driver_resolver.py`)

Bronnen: USB Printer Class, IPP, IPP-over-USB, CUPS-wachtrijen, `lpinfo` (indien
aanwezig), mDNS/netwerkdetectie (indien netwerk actief), PPD-metagegevens,
gecureerde modelcatalogus.

Printertypen: `matrix`, `inkjet`, `laser`, `thermal`, `label`, `unknown`.
Kleurcapaciteit: `monochrome`, `color`, `unknown`.
Apparaatsoort: `printer`, `multifunction`, `scanner`, `fax_multifunction`,
`unknown`.

**Belangrijk:** printtechnologie en kleurcapaciteit worden **niet** geraden
uit vrij geïnterpreteerde modelnamen. Toegestane bronnen uitsluitend: expliciete
IPP-capaciteiten, CUPS-/PPD-metagegevens, gecureerde catalogus, eenduidige
fabrikantinformatie, geteste fixtures. Bij onduidelijke data:
`technology = unknown`, `color_capability = unknown`,
`classification_status = review_required`.

### Volgorde van stuurprogramma's

1. driverless IPP (indien apparaat en omgeving dit ondersteunen)
2. reeds aanwezig distributiestuurprogramma
3. vrij generiek stuurprogramma
4. gecureerd fabrikantenpakket
5. proprietair stuurprogramma — alleen als duidelijk gelabelde optie
6. `unsupported`/`review_required`

### Matrix-/oude apparaten

Parallelle interfaces en USB-paralleladapters worden gedetecteerd zonder
functioneringsgarantie. Generieke ESC/P-/PCL-ondersteuning wordt alleen als
**kandidaat** getoond — een fysieke printtest blijft in elk geval vereist.

## Scanners (`backend/peripherals/scanner_detection.py`, `scanner_driver_resolver.py`)

Bronnen: USB-apparaatgegevens, `sane-find-scanner` (indien aanwezig),
`scanimage -L` (indien aanwezig), SANE-backendinformatie,
eSCL/AirScan (indien aanwezig), netwerk-/MFP-functie.

Scanners en printers worden **altijd apart geverifieerd**. Geen testprint en
geen scan zonder expliciete operatoractie — deze modules starten zelf geen
print- of scantaken.

## Toetsenborden, muizen en invoerapparaten (`backend/core/input_device_detection.py`)

Afgedekt: USB-toetsenborden/-muizen, Bluetooth-invoerapparaten (alleen bij
bestaande verbinding), laptoptoetsenbord, touchpad, trackpoint, touchscreen,
generiek gedetecteerde grafische tablets, gaming-HID-apparaten,
KVM-/composite-apparaten.

### Strikte privacyregel

- **geen** registratie van toetsaanslagen
- **geen** opslag van muisbewegingen
- **geen** keylogger-achtige tests
- Alleen bestaan, stuurprogrammastatus en capability-bits worden vastgelegd.

## Fysiek bewijs

Alle bovenstaande modules zijn tot nu toe alleen tegen synthetische
tekst-/sysfs-fixtures getest. Zie
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`
voor de huidige (planned) status van de fysieke verificatie.
