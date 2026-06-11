# Deploy Runner Inventory (Phase C.1)

**HEAD-Basis:** `d21e460`  
**Erzeugt:** statisches Inventar + `runner_registry.py` Classifier

## Kennzahlen

| Metrik | Wert |
|--------|------|
| Runner-Dateien (`runner_*.py`, ohne `runner_registry.py`) | **115** |
| Gesamtzeilen (Summe) | ~37k (siehe `runner_inventory.json`) |
| Device-write (heuristisch) | 8 |
| Destructive | 8 |
| Sudo (heuristisch) | 23 |
| Unknown category | 19 |

Rohdaten: `runner_inventory.txt`, `runner_inventory.json`, `runner_registry.generated.json`

## Größte Runner (Top 10)

| runner_id | Zeilen |
|-----------|--------|
| `runner_rescue_stick_readonly_build_emulation` | 1002 |
| `runner_setuphelfer_runtime_identifier_elimination` | 803 |
| `runner_rescue_sandbox_controlled_copy` | 738 |
| `runner_rescue_dry_build_orchestration` | 701 |
| `runner_laptop_failure_test_execution_readiness_final_gate` | 662 |
| `runner_rescue_build_environment_emulation` | 634 |
| `runner_rescue_build_sandbox_preparation` | 632 |
| `runner_legacy_runtime_compatibility_validation` | 617 |
| `runner_laptop_live_probe_execution_handoff` | 586 |
| `runner_rescue_debian_live_build_inputs` | 582 |

## Themencluster (Registry-Kategorien)

| Kategorie | Anzahl | Hinweis |
|-----------|--------|---------|
| `runtime` | 51 | Gates, Identifier, Version, Readiness |
| `rescue` | 16 | Rescue-Orchestrierung allgemein |
| `rescue_build` | 11 | ISO/Live-Build/Sandbox |
| `evidence` | 7 | Timelines, Snapshots, Export |
| `unknown` | 20 | konservativ — manuelle Review C.2 |
| `packaging` | 4 | Paket/Install-Pläne |
| `deploy` | 3 | Deploy-Kern |
| `rescue_usb` | 2 | Rescue-Stick/USB-Emulation |
| `backup_related` / `restore_related` | je 1 | Backup/Restore-Pläne |

## Auffällige Namensmuster

- `runner_rescue_*` — größter Cluster (~40+ Dateien)
- `runner_manual_runtime_*` — Operator-/Laptop-Failure-Ketten
- `runner_laptop_*` / `runner_lab_*` — Hardware-/Lab-Readiness
- `runner_setuphelfer_runtime_identifier_*` — Identifier-Cleanup-Zyklen

## Duplikatcluster (Audit-Hinweis, nicht refaktoriert)

- Rescue Build Pipeline: `dry_build`, `sandbox`, `assembly`, `pseudo_boot`, `debian_live`
- Evidence/Timeline: `manual_runtime_evidence_*`, `rescue_recovery_evidence_*`
- Failure Test Plans: `failure_injection`, `device_reenumeration`, `hotplug_race`, `rollback_runtime`
- ISO Readiness: `iso_readiness_*`, `iso_build_execution*`, `iso_artifact_preparation`

## Runner mit Schreib-/Systembezug (heuristisch)

**Device write / destructive (9):** u. a. ISO-Build-Execution, Sandbox-Copy, Dry-Build — Tokens `dd`/`mkfs`/`wipefs`/`sgdisk` im Quelltext.

**Sudo (24):** Install-/Package-/Privileged-Validation-Runner.

**Evidence write (54):** `write_text`/`open(...,'w')` — überwiegend Docs/Evidence unter `docs/evidence/`.

## Rescue / USB / ISO

- **ISO/Build:** `runner_rescue_iso_*`, `runner_rescue_debian_live_*`, `runner_rescue_sandbox_*`
- **USB/Stick:** `runner_rescue_stick_*` (2)
- **Storage Discovery:** `runner_rescue_storage_discovery` (read-only Plan)

## Nächste Schritte (C.2+)

- Result-Contract vereinheitlichen
- Unknown-Kategorien manuell nachschärfen
- Keine Runner-Ausführung in C.1
