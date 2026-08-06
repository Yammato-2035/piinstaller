# USB-, Drucker- und Scanner-Unterstützung — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), erweitert um
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](USB_PRINTER_SCANNER_SUPPORT_DE.md) ·
[English](USB_PRINTER_SCANNER_SUPPORT_EN.md) ·
[Français](USB_PRINTER_SCANNER_SUPPORT_FR.md) ·
[Nederlands](USB_PRINTER_SCANNER_SUPPORT_NL.md)

## USB-Geräteklassifikation (`backend/core/usb_device_detection.py`)

Erkannte Klassen (mindestens): Massenspeicher, HID, Tastatur, Maus, Drucker,
Scanner, Multifunktionsgerät, Netzwerkadapter, WLAN, Bluetooth, Audio,
Kamera, serielle Adapter, Smartcard, USB-Hub, externe GPU (nur Erkennung),
`unknown`.

Quellen: USB-Geräteklasse, Interface-Klassen, Vendor-/Product-ID,
udev-Eigenschaften, Modalias, gebundener Treiber, vorhandene
Child-Interfaces.

### Multifunktionsgeräte

Ein zusammengesetztes Gerät (z. B. Drucker+Scanner+Kartenleser) wird als
**ein Gerät mit mehreren unabhängigen Capabilities** modelliert. Jede
Funktion erhält ihren eigenen `operational_status`. Es wird nie behauptet,
eine Funktion sei betriebsbereit, nur weil eine andere Funktion desselben
Geräts erkannt wurde.

## Drucker (`backend/peripherals/printer_detection.py`, `printer_driver_resolver.py`)

Quellen: USB Printer Class, IPP, IPP-over-USB, CUPS-Queues, `lpinfo` (falls
vorhanden), mDNS/Netzwerkerkennung (falls Netzwerk aktiv), PPD-Metadaten,
kuratierter Modellkatalog.

Druckertypen: `matrix`, `inkjet`, `laser`, `thermal`, `label`, `unknown`.
Farbfähigkeit: `monochrome`, `color`, `unknown`.
Geräteart: `printer`, `multifunction`, `scanner`, `fax_multifunction`,
`unknown`.

**Wichtig:** Drucktechnologie und Farbfähigkeit werden **nicht** aus frei
interpretierten Modellnamen geraten. Zulässige Quellen sind ausschließlich:
explizite IPP-Fähigkeiten, CUPS-/PPD-Metadaten, kuratierter Modellkatalog,
eindeutige Herstellerinformationen, getestete Fixtures. Bei unklarer
Datenlage: `technology = unknown`, `color_capability = unknown`,
`classification_status = review_required`.

### Treiberreihenfolge

1. driverless IPP (sofern Gerät und Umgebung dies unterstützen)
2. bereits vorhandener Distributionstreiber
3. freier generischer Treiber
4. kuratiertes Herstellerpaket
5. proprietärer Treiber — nur als klar gekennzeichnete Option
6. `unsupported`/`review_required`

### Matrix-/Altgeräte

Parallele Schnittstellen und USB-Parallel-Adapter werden erkannt, ohne
Funktionsgarantie. Generische ESC/P-/PCL-Unterstützung wird nur als
**Kandidat** dargestellt — ein physischer Drucktest bleibt in jedem Fall
erforderlich.

## Scanner (`backend/peripherals/scanner_detection.py`, `scanner_driver_resolver.py`)

Quellen: USB-Gerätedaten, `sane-find-scanner` (falls vorhanden),
`scanimage -L` (falls vorhanden), SANE-Backend-Informationen,
eSCL/AirScan (falls vorhanden), Netzwerk-/MFP-Funktion.

Scanner und Drucker werden **immer getrennt verifiziert**. Kein Testdruck
und kein Scan wird ohne explizite Operatoraktion ausgelöst — diese Module
lösen selbst keine Druck- oder Scanvorgänge aus.

## Tastaturen, Mäuse und Eingabegeräte (`backend/core/input_device_detection.py`)

Abgedeckt: USB-Tastaturen/-Mäuse, Bluetooth-Eingabegeräte (nur bei
bestehender Verbindung), Laptop-Tastatur, Touchpad, Trackpoint,
Touchscreen, generisch erkannte Grafiktabletts, Gaming-HID-Geräte,
KVM-/Composite-Geräte.

### Strikte Datenschutzregel

- **keine** Aufzeichnung von Tastendrücken
- **keine** Speicherung von Mausbewegungen
- **keine** Keylogger-ähnlichen Tests
- Erfasst werden ausschließlich Existenz, Treiberstatus und Capability-Bits.

## Physischer Nachweis

Alle oben genannten Module wurden bislang ausschließlich gegen synthetische
Text-/sysfs-Fixtures getestet
(`backend/tests/test_usb_device_detection_v1.py`,
`test_input_device_detection_v1.py`, `test_printer_detection_v1.py`,
`test_scanner_detection_v1.py`). Siehe
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`
für den aktuellen (planned) Stand der physischen Verifikation.
