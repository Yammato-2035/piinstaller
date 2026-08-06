# FAQ : Prise en charge matérielle (FR)

Réponses courtes sur la couche de détection matérielle et de provisionnement
(PI-RS-HW-COMPAT-PROVISION-001). Pas de langage marketing.

Langues : [Deutsch](HARDWARE_SUPPORT_FAQ_DE.md) · [English](HARDWARE_SUPPORT_FAQ_EN.md) · [Français](HARDWARE_SUPPORT_FAQ_FR.md) · [Nederlands](HARDWARE_SUPPORT_FAQ_NL.md)

## Setuphelfer prend-il en charge ma carte graphique ?

Le GPU est détecté et son état (pilote lié, module chargé, firmware, périphérique
DRM, paramètres de boot actifs comme `nomodeset`) est évalué séparément. Le
fonctionnement réel de l'affichage ne peut être confirmé que par un test
physique — voir
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.

## La clé de secours installe-t-elle automatiquement des pilotes NVIDIA/propriétaires ?

Non. Les pilotes propriétaires ne sont affichés que comme **option clairement
étiquetée** (`driver_type: proprietary_optional`). Ils ne sont jamais installés
automatiquement.

## Que signifie « review_required » pour le chipset ?

Le chipset n'est nommé que si l'ID PCI, les données DMI ou une entrée de
catalogue curaté permettent une correspondance fiable. Si les données sont
insuffisantes, le système rapporte honnêtement `review_required` au lieu d'un
nom inventé.

## Puis-je utiliser immédiatement mon imprimante/scanner ?

La clé de secours indique si un pilote/backend adapté est connu et propose un
plan de pilote. Un test d'impression/scan réel n'est **pas** déclenché
automatiquement — cela reste une action volontaire de l'opérateur hors de
cette phase.

## Setuphelfer prend-il en charge tous les modèles Raspberry Pi de la même façon ?

Non. Raspberry Pi 3, 3B+, 4, 400, CM4, Pi 5 et CM5 sont détectés
individuellement via device-tree et reçoivent chacun leur propre évaluation
de support de boot et de compatibilité OS. Détails :
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_FR.md`.

## Pourquoi la clé 64 Go ne contient-elle pas simplement tous les systèmes d'exploitation ?

Parce que l'espace est limité. Setuphelfer utilise un catalogue d'images avec
sources signées, sommes de contrôle et un cache limité plutôt qu'une image
rigide « tout inclus ». Détails :
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_FR.md`.

## Cette version installe-t-elle déjà des systèmes d'exploitation ?

Non. `write_allowed` est toujours `false` pour chaque plan de provisionnement
dans cette phase. Aucune écriture n'est effectuée sur des supports réels.

## Quelles données sont envoyées au cloud ?

Uniquement un résumé rédigé (classe de plateforme, fabricant CPU/GPU, nombres
d'appareils par statut, version noyau, version payload rescue, codes d'issue).
Les numéros de série, adresses MAC/IP et données EDID complètes ne sont jamais
transmis.
