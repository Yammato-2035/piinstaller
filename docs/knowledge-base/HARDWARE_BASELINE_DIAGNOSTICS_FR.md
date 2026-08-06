# Diagnostic de référence matérielle

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) · [English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) · [Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) · [Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

## Objectif

Court contrôle de risque sûr au démarrage rescue pour RAM, CPU, GPU et stockage — avant backup/restore/install OS/GUI.

## Valeurs vérifiées

Résultats de sous-systèmes, sévérité feux, permissions du gate, codes d'issue.

## Propriétés non vérifiées

Pas de garantie longue durée, pas de garantie sans défaut, pas d'auto-tests/stress automatiques, pas d'installation pilote/firmware.

## Signification des statuts

`no_immediate_issue_detected` / `immediate_issue_detected` / `review_required` / `test_unavailable` / `not_tested` — jamais « healthy/passed ».

## Constats critiques

Les constats rouges mémoire/CPU/stockage bloquent restore et installation OS.

## Constats jaunes

Les constats jaunes produisent `review_required` et recommandent des tests étendus.

## Prochaines étapes sûres

D'abord sauver les données source, puis examiner les composants signalés ; GUI seulement avec GPU stable.

## Limites

Vert ≠ sans défaut. Outils manquants → gris/`test_unavailable`, jamais faux vert.

## Evidence

API : `/api/rescue/hardware/baseline/*`. Tests unitaires sous `backend/tests/test_*baseline*_v1.py`.

## Confidentialité

Pas de numéros de série/MAC/IP en télémétrie. Uniquement des résumés rédigés.

## Diagnostic étendu

Memtest86+, stress CPU, stress rendu GPU, auto-test SMART — uniquement avec confirmation opérateur.
