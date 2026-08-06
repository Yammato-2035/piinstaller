# Prise en charge USB, imprimantes et scanners — Rescue Stick

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](USB_PRINTER_SCANNER_SUPPORT_DE.md) · [English](USB_PRINTER_SCANNER_SUPPORT_EN.md) · [Français](USB_PRINTER_SCANNER_SUPPORT_FR.md) · [Nederlands](USB_PRINTER_SCANNER_SUPPORT_NL.md)

## Classification des périphériques USB (`backend/core/usb_device_detection.py`)

Classes détectées (minimum) : stockage de masse, HID, clavier, souris,
imprimante, scanner, périphérique multifonction, adaptateur réseau, Wi-Fi,
Bluetooth, audio, caméra, adaptateurs série, carte à puce, hub USB,
GPU externe (détection uniquement), `unknown`.

Sources : classe USB, classes d'interface, vendor/product ID, propriétés udev,
modalias, pilote lié, interfaces enfants présentes.

### Périphériques multifonction

Un appareil composite (par ex. imprimante+scanner+lecteur de cartes) est
modélisé comme **un appareil avec plusieurs capabilities indépendantes**.
Chaque fonction reçoit son propre `operational_status`. Setuphelfer n'affirme
jamais qu'une fonction est prête uniquement parce qu'une autre fonction du
même appareil a été détectée.

## Imprimantes (`backend/peripherals/printer_detection.py`, `printer_driver_resolver.py`)

Sources : USB Printer Class, IPP, IPP-over-USB, files CUPS, `lpinfo` (si
présent), découverte mDNS/réseau (si le réseau est actif), métadonnées PPD,
catalogue de modèles curaté.

Types d'imprimante : `matrix`, `inkjet`, `laser`, `thermal`, `label`, `unknown`.
Capacité couleur : `monochrome`, `color`, `unknown`.
Type d'appareil : `printer`, `multifunction`, `scanner`, `fax_multifunction`,
`unknown`.

**Important :** la technologie d'impression et la capacité couleur ne sont
**pas** déduites de noms de modèles librement interprétés. Sources autorisées
uniquement : capacités IPP explicites, métadonnées CUPS/PPD, catalogue curaté,
informations fabricant non ambiguës, fixtures testées. Si les données sont
incertaines : `technology = unknown`, `color_capability = unknown`,
`classification_status = review_required`.

### Ordre des pilotes

1. IPP sans pilote (si appareil et environnement le permettent)
2. pilote de distribution déjà présent
3. pilote générique libre
4. paquet fabricant curaté
5. pilote propriétaire — uniquement comme option clairement étiquetée
6. `unsupported`/`review_required`

### Matrice / appareils anciens

Les interfaces parallèles et adaptateurs USB-parallèle sont détectés sans
garantie de fonctionnement. Le support générique ESC/P/PCL n'est présenté
que comme **candidat** — un test d'impression physique reste toujours requis.

## Scanners (`backend/peripherals/scanner_detection.py`, `scanner_driver_resolver.py`)

Sources : données USB, `sane-find-scanner` (si présent), `scanimage -L`
(si présent), informations backend SANE, eSCL/AirScan (si présent),
fonction réseau/MFP.

Scanners et imprimantes sont **toujours vérifiés séparément**. Aucun test
d'impression ni scan n'est déclenché sans action explicite de l'opérateur —
ces modules ne lancent eux-mêmes aucun travail d'impression ou de scan.

## Claviers, souris et périphériques d'entrée (`backend/core/input_device_detection.py`)

Couvert : claviers/souris USB, périphériques Bluetooth (uniquement s'ils sont
déjà connectés), clavier d'ordinateur portable, pavé tactile, trackpoint,
écran tactile, tablettes graphiques détectées génériquement, périphériques
HID de jeu, appareils KVM/composites.

### Règle stricte de confidentialité

- **aucune** enregistrement de frappes
- **aucun** stockage de mouvements de souris
- **aucun** test de type keylogger
- Seuls l'existence, l'état du pilote et les bits de capability sont capturés.

## Preuve physique

Tous les modules ci-dessus n'ont jusqu'ici été testés que contre des fixtures
synthétiques texte/sysfs. Voir
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`
pour l'état actuel (planned) de la vérification physique.
