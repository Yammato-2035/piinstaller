# Raspberry Pi 3 à 5 — Modèle de support

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](RASPBERRY_PI_3_TO_5_SUPPORT_DE.md) ·
[English](RASPBERRY_PI_3_TO_5_SUPPORT_EN.md) ·
[Français](RASPBERRY_PI_3_TO_5_SUPPORT_FR.md) ·
[Nederlands](RASPBERRY_PI_3_TO_5_SUPPORT_NL.md)

## Message principal

**Il n'existe pas d'affirmation générale « Raspberry Pi 3–5 pris en
charge ».** Chaque combinaison de carte, architecture, système
d'exploitation, support de démarrage et version d'image est évaluée
individuellement :

```
Carte × architecture × système d'exploitation × support de démarrage × version d'image × statut de test
```

Le Raspberry Pi 3 peut avoir des exigences d'architecture, de mémoire et
de démarrage différentes de celles du Raspberry Pi 5.

## Familles de plateformes couvertes

- Raspberry Pi 3 / 3B+
- Raspberry Pi 4
- Raspberry Pi 400
- Compute Module 4 (dans la mesure où il est détectable génériquement via
  le device tree)
- Raspberry Pi 5
- Compute Module 5 (uniquement si détectable de manière fiable dans la
  pile actuelle)

## Modules

| Module | Objectif |
|---|---|
| `backend/platforms/raspberry_pi_detection.py` | Détection exacte du modèle via `/proc/device-tree/model`, `/proc/device-tree/compatible`, informations SoC, taille de la RAM |
| `backend/platforms/raspberry_pi_boot_plan.py` | Prise en charge du support de démarrage (microSD, stockage de masse USB, NVMe sur Pi 5, démarrage réseau comme `future/experimental`) |
| `backend/platforms/raspberry_pi_compatibility.py` | Résumé de compatibilité par modèle |
| `backend/platforms/raspberry_pi_os_plan.py` | Matrice des systèmes candidats par modèle/RAM/architecture |

## Sources de détection

- `/proc/device-tree/model`, `/proc/device-tree/compatible`
- Informations SoC et architecture (`aarch64`/`armv7`)
- Support de démarrage
- Statut EEPROM/bootloader — **lecture seule**, aucune modification
- Taille de la RAM
- Interfaces réseau, statut WiFi/Bluetooth
- Contrôleurs USB, stockage, PCIe/NVMe (Pi 5)
- Informations HAT/overlay, si détectables
- Interfaces caméra/écran — détection uniquement, aucune activation

## Valeurs de statut

- `boot_supported`
- `bootloader_update_recommended`
- `bootloader_update_required`
- `storage_supported`
- `os_compatible`
- `physical_validation_required`

## Matrice des systèmes d'exploitation (préparation)

| Catégorie | Statut de support |
|---|---|
| Raspberry Pi OS | entrée de catalogue actuelle (voir `data/provisioning/os_catalog.json`) |
| Debian ARM64 | entrée de catalogue actuelle |
| Ubuntu Server ARM64 | entrée de catalogue actuelle |
| Ubuntu Desktop ARM64 | optionnel |
| autres systèmes | `future`/`unsupported` |

## Numéro de série/confidentialité

Les numéros de série sont **traités localement uniquement de manière
caviardée**, jamais transmis en clair. Pour une éventuelle liaison
d'appareil, seul un hash salé et stable est utilisé — jamais une valeur
brute.

## Aucune modification EEPROM dans cette phase

Le statut du bootloader/EEPROM est exclusivement **lu**. Une mise à jour
de l'EEPROM ne fait pas partie de cette phase et reste réservée à
`PI-RS-HW-ACTIVATE-002`.

## Preuve physique

Les modules actuels ont été testés avec des fixtures de device tree
synthétiques (`backend/tests/test_raspberry_pi_detection_v1.py`,
`test_raspberry_pi_os_compatibility_v1.py`). Un test physique sur des
cartes réelles reste à faire — voir
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.
Aucun modèle ne peut être qualifié de « vérifié » sans preuve physique.
