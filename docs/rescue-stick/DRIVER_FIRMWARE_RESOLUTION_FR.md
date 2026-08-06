# Résolution des pilotes et du firmware — Rescue Stick

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](DRIVER_FIRMWARE_RESOLUTION_DE.md) · [English](DRIVER_FIRMWARE_RESOLUTION_EN.md) · [Français](DRIVER_FIRMWARE_RESOLUTION_FR.md) · [Nederlands](DRIVER_FIRMWARE_RESOLUTION_NL.md)

Voir aussi : [`docs/architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md`](../architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md).

## Objectif

Les données brutes de l'inventaire matériel deviennent une **proposition**
d'activation pilote/firmware — sans l'exécuter.

## Étapes du résolveur (`backend/core/driver_resolver.py`)

1. Évaluer le modalias noyau
2. Vérifier le pilote lié (`kernel_driver_in_use`)
3. Vérifier les modules noyau disponibles (`modinfo`/`lsmod`)
4. Vérifier les erreurs firmware (`backend/core/firmware_resolver.py`)
5. Vérifier les informations de paquets installés
6. Prendre en compte distribution/architecture
7. Appliquer les quirks curatés (`hardware_compat_catalog.py`)
8. Produire un plan d'activation sûr (`driver_activation_plan.py`)

Toute étape peut s'arrêter tôt avec `unknown` ou `review_required` si les
données sont insuffisantes — Setuphelfer **ne suppose pas**.

## DriverPlan

`live_activation_possible` et `persistent_install_possible` sont de purs
champs d'évaluation — aucun module ne les transforme en action réelle.

## Niveaux de confiance des sources de paquets

1. déjà présent dans l'image rescue
2. dépôts officiels de la distribution
3. cache hors ligne Setuphelfer signé
4. dépôt fabricant officiel
5. paquet signé fourni manuellement
6. source inconnue → **bloqué**

## Explicitement interdit

- scripts shell fabricant non vérifiés (`curl|bash`)
- téléchargement sans somme de contrôle ou sans TLS
- ajout automatique de sources de paquets
- acceptation automatique de conditions de licence
- installation automatique de pilotes GPU propriétaires
- listes noires permanentes de modules noyau
- modification des clés Secure Boot/MOK

## Résolveur firmware (`backend/core/firmware_resolver.py`)

Le statut firmware est évalué **séparément** du statut pilote
(`present|missing|unknown|not_required`). Un pilote chargé sans firmware
adapté est `firmware_missing`, pas `ready`.
