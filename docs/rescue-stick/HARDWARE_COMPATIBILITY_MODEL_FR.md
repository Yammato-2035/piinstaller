# Modèle de compatibilité matérielle — Clé de secours (Rescue Stick)

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](HARDWARE_COMPATIBILITY_MODEL_DE.md) ·
[English](HARDWARE_COMPATIBILITY_MODEL_EN.md) ·
[Français](HARDWARE_COMPATIBILITY_MODEL_FR.md) ·
[Nederlands](HARDWARE_COMPATIBILITY_MODEL_NL.md)

## Message principal

**La détection n'est pas une garantie de fonctionnement.** Pour chaque
périphérique, la clé de secours affiche un état traçable à plusieurs
niveaux plutôt qu'une simple réponse oui/non.

## Feu tricolore de statut (interface Rescue)

| Feu | Signification |
|---|---|
| 🟢 Vert | détecté, pilote chargé, firmware présent, périphérique opérationnel |
| 🟡 Jaune | détecté mais limité / pilote optionnel / test physique requis / capacité non entièrement vérifiée |
| 🔴 Rouge | pilote manquant, firmware manquant, noyau incompatible, périphérique bloqué, activation sûre impossible |
| ⚪ Gris | inconnu, non vérifié, outil manquant, aucune classification fiable |

Ce feu tricolore est implémenté dans `frontend/src/rescue/RescueHardwarePanel.tsx`
et `frontend/src/rescue/rescue-shell.css` (`.rescue-hw-badge-*`). Le
diagnostic de référence matériel séparé (RAM/CPU/GPU/stockage) utilise un
feu tricolore analogue mais indépendant — voir
`HARDWARE_BASELINE_DIAGNOSTICS_FR.md`.

## Classes matérielles couvertes

1. CPU et SoC (`backend/core/cpu_platform_detection.py`)
2. GPU/chemins graphiques (`backend/core/gpu_detection.py`, `gpu_driver_resolver.py`)
3. Cartes mères et chipsets (`backend/core/mainboard_chipset_detection.py`)
4. Périphériques PCI/PCIe (`backend/core/hardware_inventory.py::collect_pci_devices`)
5. Périphériques USB (`backend/core/usb_device_detection.py`)
6. Stockage de masse/contrôleurs (`hardware_inventory.py::collect_storage_controllers`)
7. Adaptateurs réseau (`hardware_inventory.py::collect_network_devices`)
8. Claviers/souris (`backend/core/input_device_detection.py`)
9. Imprimantes (`backend/peripherals/printer_detection.py`)
10. Scanners (`backend/peripherals/scanner_detection.py`)
11. Raspberry Pi 3–5 (`backend/platforms/raspberry_pi_*.py`) — voir
    `RASPBERRY_PI_3_TO_5_SUPPORT_FR.md`
12. Préparation du provisionnement multi-architecture — voir
    `MULTI_ARCH_PROVISIONING_MODEL_FR.md`

## Règle d'architecture : pas de catalogue de masse codé en dur

Des milliers de périphériques ne sont **pas** codés en dur dans le code
source. À la place :

```
IDs matériels/informations système
  → HardwareDevice normalisé (backend/core/hardware_contracts.py)
  → résolution générique de pilotes/firmware (backend/core/driver_resolver.py)
  → petite base de compatibilité organisée pour les cas particuliers
    (data/hardware/hardware_compat_catalog.json)
  → planification d'activation sûre (backend/core/driver_activation_plan.py, aperçu uniquement)
  → vérification traçable (références d'evidence, matrice de tests physiques)
```

## Résolution des pilotes et du firmware

La résolution des pilotes/firmware (`backend/core/driver_resolver.py`,
`backend/core/driver_activation_plan.py`) suit le même ordre pour chaque
classe de périphérique détectée :

1. pilote déjà présent dans le noyau/la distribution en cours d'exécution
2. pilote libre et générique du dépôt standard
3. paquet fournisseur organisé (`data/hardware/hardware_compat_catalog.json`)
4. pilote propriétaire — uniquement comme option clairement identifiée
   nécessitant une confirmation manuelle (`driver_type: proprietary_optional`)
5. `unsupported`/`review_required` si aucun des niveaux ci-dessus ne s'applique

Le firmware suit le même principe : sa présence est détectée et évaluée,
son absence est signalée — une activation automatique du firmware ou un
téléchargement automatique de firmware **n'a pas lieu** dans cette phase de
développement. Chaque plan d'activation (`driver_activation_plan.py`) est
exclusivement un aperçu (`preview-only`), jamais une action d'écriture ou
d'installation exécutée.

## Exemple : périphérique multifonction

Un « appareil multifonction HP » est modélisé comme **un seul
périphérique avec plusieurs capacités**, et non comme un statut global
unique « fonctionne » :

```
Périphérique : appareil multifonction HP
Fonctions :
  - printer   → operational_status propre
  - scanner   → operational_status propre
  - storage_card_reader → operational_status propre
```

Il n'est **jamais** affirmé que le scanner fonctionne uniquement parce que
la fonction d'impression a été détectée.

## Pilotes propriétaires

Les pilotes propriétaires (p. ex. le module NVIDIA complet) sont présentés
comme un **candidat optionnel** (`driver_type: proprietary_optional`),
jamais installés automatiquement. Chaque option propriétaire nécessite une
vérification manuelle distincte par l'opérateur.

## Phase suivante

L'installation réelle des pilotes, l'activation du firmware, les tests
fonctionnels d'imprimante/scanner et les tests de démarrage physiques du
Raspberry Pi ne sont traités que dans `PI-RS-HW-ACTIVATE-002`.
