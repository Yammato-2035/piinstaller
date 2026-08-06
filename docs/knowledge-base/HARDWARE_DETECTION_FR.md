# Base de connaissances : Détection matérielle sur la clé de secours

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16). Public : utilisateurs et support.

Langues : [Deutsch](HARDWARE_DETECTION_DE.md) · [English](HARDWARE_DETECTION_EN.md) · [Français](HARDWARE_DETECTION_FR.md) · [Nederlands](HARDWARE_DETECTION_NL.md)

## Que fait la clé de secours avec mon matériel ?

Elle détecte les appareils en lecture seule via les mécanismes Linux existants
(sysfs, IDs PCI/USB, modalias noyau) et évalue leur état opérationnel en
plusieurs étapes : détecté → pilote connu → pilote présent → module chargé →
firmware présent → prêt. Elle n'apporte **aucune** modification à votre système.

## « Détecté » signifie-t-il que l'appareil fonctionne ?

**Non.** La détection est la première étape, pas une garantie de fonctionnement.
Un appareil peut être détecté mais bloqué sans module noyau adapté, sans
firmware, ou par un paramètre de boot.

## Que montrent les feux de signalisation ?

- 🟢 Vert : détecté, pilote chargé, firmware présent, prêt
- 🟡 Jaune : utilisable de façon limitée, pilote optionnel, test physique requis
- 🔴 Rouge : pilote/firmware manquant, noyau incompatible, bloqué
- ⚪ Gris : inconnu, non vérifié, outil manquant

## Qu'est-ce qu'un « plan de pilote » ?

Un plan de pilote est une **proposition** indiquant quel pilote/paquet
conviendrait — avec niveau de confiance de la source, notes de licence et
impact Secure Boot. Ce n'est **pas** une installation.

## Pourquoi imprimantes/scanners ne sont-ils pas toujours classés clairement ?

La technologie d'impression et la capacité couleur ne sont dérivées que de
sources fiables (capacités IPP, métadonnées CUPS/PPD, catalogue curaté) —
jamais d'un nom de modèle inventé. Si les données sont floues :
`unknown`/`review_required`.

## Que se passe-t-il avec un appareil multifonction ?

Les fonctions imprimante, scanner et autres du même appareil sont évaluées
**séparément**.

## Raspberry Pi 3–5 est-il pleinement pris en charge ?

Il n'y a pas d'affirmation globale. Chaque combinaison carte/architecture/OS/
support de boot est évaluée individuellement. Détails :
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_FR.md`.

## Pourquoi toutes les images OS ne tiennent-elles pas sur la clé 64 Go ?

Une clé 64 Go ne peut pas contenir un nombre illimité d'images complètes.
Setuphelfer utilise un catalogue d'images signées et un cache limité. Détails :
`docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_FR.md`.
