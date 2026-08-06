# Architecture du support 64 Go — Rescue Stick

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](64GB_CARRIER_ARCHITECTURE_DE.md) · [English](64GB_CARRIER_ARCHITECTURE_EN.md) · [Français](64GB_CARRIER_ARCHITECTURE_FR.md) · [Nederlands](64GB_CARRIER_ARCHITECTURE_NL.md)

## Principe

**Une seule clé 64 Go ne peut pas contenir un nombre illimité d'images
système complètes.** Setuphelfer utilise donc un catalogue, un cache limité
et des images signées plutôt qu'une approche « tout sur la clé ».

## Variantes comparées (`backend/rescue/carrier_layout.py`)

| Variante | Description | Prérequis |
|---|---|---|
| **A — Universal** | Une clé démarre nativement x86_64 et Raspberry Pi | chemin de boot partagé prouvé et validé (n'existe **pas** actuellement) |
| **B — Split Carriers** | Catalogue de build commun, mais supports x86 et ARM/Pi séparés | deux supports physiques nécessaires |
| **C — Orchestrator Cache** | Clé rescue/orchestrateur universelle avec images cibles téléchargeables/en cache | défaut lorsqu'aucun chemin de boot universel n'est prouvé |

### Décision

Comme ce dépôt n'a **aucune preuve** d'un secteur de boot/ESP partagé validé
pour x86_64 (BIOS/UEFI) **et** le boot SD/EEPROM Raspberry Pi, la
**variante C (orchestrator cache)** est le défaut conforme à la spécification.
`evaluate_carrier_strategy()` marque la variante A comme `decided` uniquement
si l'appelant passe explicitement `universal_boot_path_evidence=True` avec
une preuve réelle.

Ceci est une documentation intermédiaire fondée sur des preuves — pas une
décision produit définitive.

## Plan de capacité (`backend/rescue/carrier_capacity_planner.py`)

Le plan utilise les **octets réels du support**, pas une hypothèse forfaitaire
de 64 Go. Une réserve de sécurité d'**au moins 10 %** est prévue. La
découverte réelle réutilise `storage_facade` — pas de nouvelle logique `lsblk`.

## Contenu possible du support (`backend/rescue/carrier_content_catalog.py`)

- Setuphelfer Rescue Runtime
- chemin de boot x86_64
- assets de boot ARM/Pi optionnels si validés
- catalogue matériel (`data/hardware/`)
- paquets hors ligne pilotes/firmware
- catalogue d'images (`data/provisioning/os_catalog.json`)
- cache d'images limité
- zone evidence/logs
- métadonnées de mise à jour et de signature

## Hors périmètre de cette phase

**Pas de partitionnement.** `carrier_layout.py` et
`carrier_capacity_planner.py` produisent uniquement des plans/évaluations —
aucune écriture sur des supports réels.
