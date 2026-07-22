# FAQ PI-RS-ASUS-CAPTURE-FINALIZE-004 (FR)

1. **Pourquoi pas d'interface graphique ?** Mode texte (`setuphelfer_mode=text`, `skip_gui`). Statut GUI : `not_applicable_for_text_hardware_discovery`.
2. **Pourquoi `nomodeset` ?** Sans cela, amdgpu créait un périphérique factice et l'écran restait noir sur G513QM.
3. **État terminal ?** Un seul statut `complete|partial|failed|cancelled` avec `terminal=true`.
4. **Retrait de la clé ?** Seulement après le message de fin et le marqueur Completion/Partial.
5. **Pas de logs Panther ?** `windows_setup_logs=not_found` (pas `failed`).
6. **Numéros de série complets ?** Uniquement sur la clé dans `protected_raw`.
7. **Effacer au dernier commit ?** Insuffisant si d'anciens commits restent accessibles.
8. **`diagnosis_incomplete` ?** Capture non terminale ou zones obligatoires manquantes.
