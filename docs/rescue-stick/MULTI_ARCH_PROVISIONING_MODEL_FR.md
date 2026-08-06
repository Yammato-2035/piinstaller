# Modèle de provisionnement multi-architecture — Rescue Stick

État : PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), complété par
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](MULTI_ARCH_PROVISIONING_MODEL_DE.md) · [English](MULTI_ARCH_PROVISIONING_MODEL_EN.md) · [Français](MULTI_ARCH_PROVISIONING_MODEL_FR.md) · [Nederlands](MULTI_ARCH_PROVISIONING_MODEL_NL.md)

## Principe

**Les installations réelles de systèmes d'exploitation restent bloquées
jusqu'à la prochaine porte de validation.** Cette phase fournit uniquement
un catalogue d'images, des contrôles de compatibilité, un aperçu de
vérification et un plan d'installation — **aucune** écriture.

## Modules

| Module | Objet |
|---|---|
| `backend/provisioning/os_catalog.py` | Charge/filtre/valide `data/provisioning/os_catalog.json` ; impose `download_enabled=false` |
| `backend/provisioning/os_compatibility.py` | Vérifie architecture/plateforme/taille cible contre l'entrée catalogue |
| `backend/provisioning/os_image_verifier.py` | SHA256 pour fichiers locaux, aperçu de vérification — **aucun** téléchargement |
| `backend/provisioning/os_install_plan.py` | Produit un aperçu `OsInstallPlan`, `write_allowed` toujours `false` |

## Premières catégories de catalogue autorisées

**x86_64 :** Debian Stable, Ubuntu LTS, Linux Mint Stable.

**ARM/Raspberry Pi :** Raspberry Pi OS, Debian ARM64, Ubuntu Server ARM64.

Les autres catégories sont préparées uniquement comme `support_status: "future"`.

## Plan de provisionnement

`write_allowed` est **toujours `false`** dans cette phase —
`backend/tests/test_provisioning_os_plan_v1.py` le vérifie explicitement.

## Interdit dans cette phase

- pas de `dd` sur supports cibles réels
- pas de `mkfs`, `parted`, `sfdisk`, `sgdisk`, `wipefs`
- pas de modification des partitions EFI internes
- pas d'installation OS automatique
- pas de téléchargement d'image (`download_enabled` reste `false`)

## Prochaine étape

`PI-RS-HW-ACTIVATE-002` traite le téléchargement d'images signées et
l'écriture OS contrôlée exclusivement sur des supports de test explicitement
approuvés.
