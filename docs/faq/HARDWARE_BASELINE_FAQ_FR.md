# FAQ : Diagnostic de référence matérielle (FR)

Questions obligatoires pour PI-RS-HW-BASELINE-DIAG-I18N-002. Réponses courtes et honnêtes.

Langues : [Deutsch](HARDWARE_BASELINE_FAQ_DE.md) · [English](HARDWARE_BASELINE_FAQ_EN.md) · [Français](HARDWARE_BASELINE_FAQ_FR.md) · [Nederlands](HARDWARE_BASELINE_FAQ_NL.md)

## 1. Une tuile verte signifie-t-elle que le matériel est garanti sans défaut ?

Non. `no_immediate_issue_detected` signifie seulement que le court test de baseline n'a trouvé aucun problème immédiat. Il ne remplace pas un test long et ne garantit jamais un matériel sans défaut.

## 2. Que vérifie le test mémoire rapide ?

L'inventaire (`/proc/meminfo`, DMI optionnel), les signaux noyau (EDAC/MCE/OOM) et une sonde rapide bornée (au plus 128 MiB ou 2 % de MemAvailable, délai maximum).

## 3. Pourquoi ne remplace-t-il pas un Memtest complet ?

Un Memtest complet prend des heures et sollicite toute la RAM. La baseline est volontairement courte et sûre et ne démarre jamais Memtest86+/memtester automatiquement.

## 4. Que vérifie-t-on pour le CPU ?

Les données de plateforme (via `cpu_platform_detection`), les messages machine-check/hardware-error, l'état thermique/throttling et une courte sonde déterministe.

## 5. Pourquoi aucun long test de stress CPU n'est-il démarré automatiquement ?

Les tests longs (stress-ng/Prime95) génèrent charge et chaleur. Ils exigent une confirmation opérateur et appartiennent aux tests étendus, pas à la baseline.

## 6. Que vérifie-t-on pour le GPU ?

La détection via `gpu_detection`, les render nodes, les erreurs noyau/firmware et des sondes optionnelles en lecture seule (`glxinfo`/`eglinfo`/`vulkaninfo`). Pas de stress de rendu.

## 7. Pourquoi une sauvegarde peut-elle rester possible malgré un GPU défectueux ?

Le gate baseline bloque le mode GUI pour un GPU rouge, mais pas automatiquement la sauvegarde. La sauvegarde est orientée lecture et n'a pas besoin d'un affichage stable.

## 8. Quelles valeurs HDD sont critiques ?

SMART overall FAILED, Pending Sectors, Offline Uncorrectable et erreurs I/O noyau répétées. Reallocated Sectors et erreurs CRC sont des avertissements jaunes.

## 9. Que signifient les Pending Sectors ?

Des secteurs que le disque a marqués comme problématiques et qui n'ont pas encore été remappés. C'est un constat critique qui priorise le sauvetage des données.

## 10. Quelles valeurs SATA SSD sont vérifiées ?

Wear Leveling, Available Reserved Space, Reported Uncorrectable, UDMA CRC, Unexpected Power Loss et support TRIM via sysfs.

## 11. Quelles valeurs NVMe sont critiques ?

Critical Warning ≠ 0, Available Spare ≤ Threshold, Percentage Used ≥ 100 %, Media/Data Integrity Errors et resets contrôleur répétés.

## 12. Pourquoi Setuphelfer ne démarre-t-il pas automatiquement un auto-test SMART ?

Les auto-tests SMART peuvent être longs et charger le disque. La baseline lit seulement les attributs existants ; les auto-tests nécessitent une confirmation opérateur.

## 13. Que se passe-t-il en cas de constat de stockage critique ?

Restore et installation OS sont bloqués par le gate. La sauvegarde depuis le disque source reste possible pour encore sauver les données.

## 14. Un disque signalé peut-il encore servir de cible de sauvegarde ?

Non. Un disque cible rouge ne doit pas être écrit. Comme source d'une sauvegarde d'urgence, un disque signalé reste lisible.

## 15. Quels tests nécessitent une confirmation opérateur ultérieure ?

Memtest86+, stress CPU, stress de rendu GPU, SMART short/extended self-test. La baseline n'en démarre aucun automatiquement.

## 16. Quelles données sont envoyées au serveur de télémétrie ?

Uniquement des résumés rédigés (classe de plateforme, classe fabricant CPU/GPU, compteurs de statut, codes d'issue, version noyau/payload).

## 17. Les numéros de série sont-ils transmis ?

Non. Numéros de série, adresses MAC, adresses IP et données EDID complètes ne sont jamais transmis.

## 18. Quelles différences existe-t-il entre Pi 3, Pi 4 et Pi 5 ?

Ils sont détectés individuellement via device tree et reçoivent leurs propres évaluations de support de boot et de compatibilité OS. Détails : `RASPBERRY_PI_3_TO_5_SUPPORT_FR.md`.

## 19. Une seule clé 64 Go peut-elle contenir tous les systèmes d'exploitation ?

Non. Setuphelfer utilise un catalogue plus un cache limité plutôt que « tout sur la clé ». Détails : `64GB_CARRIER_ARCHITECTURE_FR.md`.

## 20. Quand un test matériel physique est-il requis ?

Dès que la baseline signale rouge/jaune, que des outils manquent (`test_unavailable`), ou qu'une fonction réelle (GUI, impression, scan, boot) doit être confirmée.
