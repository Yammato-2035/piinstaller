# Diagnostic de référence matérielle — Rescue Stick

État : PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Langues : [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) ·
[English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) ·
[Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) ·
[Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

Voir aussi : [Hardware Compatibility Model (FR)](HARDWARE_COMPATIBILITY_MODEL_FR.md).

> Note de traduction : cette édition est structurellement complète et alignée
> sur le contenu. Une relecture linguistique native peut encore être en
> attente.

## 1. Objectif de la baseline matérielle précoce

La baseline matérielle précoce est un **contrôle de risque court et sûr** au
démarrage du système de secours. Elle examine mémoire, CPU, GPU et stockages
pour détecter des problèmes immédiats — avant sauvegarde, restauration,
installation OS ou mode GUI.

Elle ne remplace ni Memtest86+, ni les self-tests SMART, ni les benchmarks de
stress. Contrat : `backend/core/hardware_baseline_contracts.py`.
Orchestration : `backend/rescue/hardware_baseline_orchestrator.py`.

## 2. Couleurs du feu et vocabulaire BaselineStatus

| Feu (`BaselineSeverity`) | Statuts typiques (`BaselineStatus`) |
|---|---|
| 🟢 `green` | `no_immediate_issue_detected` |
| 🟡 `yellow` | `degraded`, `review_required`, `extended_test_recommended` |
| 🔴 `red` | `immediate_issue_detected`, `extended_test_required` |
| ⚪ `gray` | `test_unavailable`, `not_tested` |

Signification des statuts :

| Statut | Signification |
|---|---|
| `no_immediate_issue_detected` | Aucun signal aigu dans les contrôles rapides ; **pas** une garantie sans défaut |
| `immediate_issue_detected` | Constat aigu (ex. MCE, alerte SMART/NVMe critique, hang GPU noyau) |
| `degraded` | État dégradé ; fonctionnement possible mais notable |
| `review_required` | Revue opérateur nécessaire (données floues ou contradictoires) |
| `extended_test_recommended` | Test long recommandé ; jamais démarré automatiquement |
| `extended_test_required` | Test long requis avant opérations d’écriture critiques |
| `test_unavailable` | Outil/capteur absent ; contrôle omis, pas « réussi » |
| `not_tested` | Sous-système pas encore examiné |

Il n’existe **aucun** statut du type `healthy`, `ok` ou `passed`. Les
affirmations interdites sont dans `FORBIDDEN_BASELINE_CLAIMS`.

## 3. Baseline mémoire (`memory_baseline_diagnostics.py`)

Contrôles additifs :

1. **Inventaire** — `/proc/meminfo`, optionnellement `dmidecode -t memory`
2. **Erreurs noyau/matériel** — signaux EDAC / MCE / OOM via `dmesg`
3. **Plausibilité** — capacité physique déclarée vs. utilisable par le noyau
4. **Quick probe** — tampon in-process borné, au plus **128 MiB** ou
   **2 % de `MemAvailable`** (le plus petit des deux) ; jamais un Memtest
   complet, jamais d’installation de `memtester` / `stress-ng` / `rasdaemon`

## 4. Baseline CPU (`cpu_baseline_diagnostics.py`)

S’appuie sur `cpu_platform_detection` et ajoute :

- scan MCE / hardware-error / lockup / watchdog (`dmesg`)
- températures thermiques et indices de throttling (`sysfs`)
- quick probe borné et déterministe

**Jamais** `stress-ng`, Prime95 ou charge durable similaire. Pas de mise à
jour microcode/BIOS.

## 5. Baseline GPU (`gpu_baseline_diagnostics.py`)

Réutilise `gpu_detection.build_gpu_report` comme seule source d’inventaire et
ajoute :

- nœuds de rendu (`/dev/dri/renderD*`)
- erreurs noyau/firmware (hang, reset, fence timeout, Xid)
- probes optionnelles en lecture seule : `glxinfo` / `eglinfo` / `vulkaninfo`

Pilote/firmware manquant → typiquement `yellow`/`review_required`. Erreurs
GPU noyau critiques → `red`. Pas d’installation de pilote, pas d’écriture
modprobe/cmdline.

## 6. Baseline HDD / SATA-SSD / NVMe

Couche commune : `storage_baseline_diagnostics.py` (erreurs I/O noyau,
disponibilité des outils). Classes :

| Classe | Module | Sources typiques |
|---|---|---|
| HDD | `hdd_baseline_diagnostics.py` | attributs `smartctl` (dont 5/197/198/199/194) |
| SATA-SSD | `sata_ssd_baseline_diagnostics.py` | usure/spare/uncorrectable/CRC, TRIM |
| NVMe | `nvme_baseline_diagnostics.py` | `nvme smart-log` / `nvme id-ctrl` |

Seuls les attributs SMART/NVMe **déjà présents** sont lus. Un self-test SMART
(`smartctl -t`, self-tests NVMe étendus) n’est **jamais démarré
automatiquement**.

## 7. Limites des tests rapides

- 🟢 `green` / `no_immediate_issue_detected` ne signifie **pas** que le
  matériel est sans défaut ou stable à long terme.
- Un quick probe ne couvre qu’une minuscule portion mémoire/CPU.
- Outils manquants → `test_unavailable` / `gray`, pas « tout va bien ».
- Les tests étendus (Memtest86+, SMART self-test, stress rendu GPU) sont hors
  de ce chemin rapide.

## 8. `HardwareBaselineGate`

Implémentation : `backend/rescue/hardware_baseline_gate.py`.

Champs (additifs par rapport à `core.safety_facade`, **jamais** un contournement) :

| Champ | Rôle |
|---|---|
| `backup_allowed` | la sauvegarde d’urgence en lecture reste en principe possible |
| `restore_allowed` | restauration seulement sans constat data-critical rouge et après contrôles complets |
| `os_installation_allowed` | installation OS analogue à la restauration |
| `gui_mode_allowed` | GUI seulement sans constat GPU rouge |

Les deux couches doivent s’accorder : porte baseline **et** `safety_facade`.

## 9. Effets des constats critiques

| Constat | Effet |
|---|---|
| Rouge mémoire / CPU / stockage (agrégé) | bloque restauration et installation OS |
| Rouge GPU | bloque la GUI (`gui_mode_allowed=false`), **pas** la sauvegarde |
| Disque **source** rouge | reste sauvegardable (lire est le but de la sauvegarde d’urgence) |
| Disque **cible** rouge | jamais inscriptible pour destination de backup, restore ou installation OS |

Évaluation par opération : `evaluate_operation_against_baseline_gate`.

## 10. Routes API (lecture seule / bornées)

Module : `backend/api/routes/rescue_hardware_baseline.py`.

| Méthode | Chemin | But |
|---|---|---|
| `GET` | `/api/rescue/hardware/baseline/status` | état gate/run ou `{has_run:false}` |
| `POST` | `/api/rescue/hardware/baseline/quick` | lancer la baseline rapide |
| `POST` | `/api/rescue/hardware/baseline/extended-preview` | mêmes contrôles, recommandations mises en avant |
| `GET` | `/api/rescue/hardware/baseline/latest` | dernier run complet |
| `GET` | `/api/rescue/hardware/baseline/memory` | sous-système mémoire |
| `GET` | `/api/rescue/hardware/baseline/cpu` | sous-système CPU |
| `GET` | `/api/rescue/hardware/baseline/gpu` | sous-système GPU |
| `GET` | `/api/rescue/hardware/baseline/storage` | tous les résultats stockage |
| `GET` | `/api/rescue/hardware/baseline/storage/{device_id}` | un périphérique |

Aucune route ne lance d’installation, de mise à jour firmware, de formatage
ou de self-test SMART.

## 11. Les tests étendus exigent une confirmation opérateur

`ExtendedTestRecommendation.operator_confirmation_required` vaut `true` par
défaut. `/extended-preview` ne fait que présenter des recommandations
(`memtest86plus`, `cpu_stress`, `gpu_render_stress`, `smart_self_test_short`,
…) et ne démarre aucun test long. Tout test étendu exige une **action
opérateur explicite et séparée** hors de cette API.

## 12. Protection des données

La télémétrie baseline suit `telemetry_redaction_contract.py` /
`hardware_dcc_status.py` : **pas de numéros de série, pas d’adresses MAC,
pas d’adresses IP** dans les payloads de télémétrie. Les `device_id` restent
des noms de périphériques bloc techniques (ex. `sda`, `nvme0n1`), pas des
séries matérielles.
