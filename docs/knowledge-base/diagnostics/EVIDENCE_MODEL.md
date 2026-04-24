# Evidence Model (DIAG-1.1)

Dieses Modell definiert, wie Test- und Fehlererkenntnisse strukturiert gespeichert werden.

## Ziele

- Reproduzierbare Diagnose-Evidenz statt Chat-Freitext.
- Trennung von Symptom, vermuteter Ursache und bestaetigter Root-Cause.
- Rueckkopplung in Diagnosekatalog, Regeln, FAQ und Tests.

## EvidenceRecord

Pflichtfelder:

- `id`, `timestamp`
- `source_type` (`manual_test`, `api_test`, `unit_test`, `vm_test`, `hardware_test`, `user_report`)
- `domain`, `platform`
- `scenario`, `test_goal`
- `outcome` (`success`, `partial`, `failed`, `inconclusive`)
- `severity`, `confidence`
- `system_profile_id`
- `storage_profile`, `encryption_profile`, `boot_profile`
- `observed_symptoms`, `raw_signals`
- `matched_diagnosis_ids`
- `diagnosis_links[]` mit `status` (`suspected`, `confirmed`, `refuted`)
- `suspected_root_causes`, `confirmed_root_cause`
- `corrective_actions`, `unresolved_questions`
- `docs_updated`, `faq_updated`, `catalog_updated`, `tests_added`

## SystemProfile

Pflichtfelder:

- `id`, `platform_class`
- `cpu_model`, `cpu_arch`, `core_count`, `ram_total_mb`
- `os_name`, `os_version`, `kernel_version`
- `boot_mode`
- `filesystem_root`, `filesystem_backup_target`
- `storage_devices[]`

Optional:

- `hostname`, `manufacturer`, `model`, `network_summary`

## Datenschutzgrenzen

- Keine unnötigen personenbezogenen Daten.
- Nur diagnose-relevante technische Kontexte speichern.
- Keine zufaelligen Hostdetails ohne Mehrwert fuer Fehlerklassifikation.

## Ablage

- Evidence: `data/diagnostics/evidence/*.json`
- Profiles: `data/diagnostics/profiles/*.json`
