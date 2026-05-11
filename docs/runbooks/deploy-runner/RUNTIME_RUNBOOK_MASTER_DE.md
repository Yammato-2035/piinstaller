# Runtime Runbook Master (DE)

## Zweck
Dieses Dokument buendelt alle sieben manuellen Runtime-Runbooks. Keine automatische Ausfuehrung.

## Scope
Runner Runtime Execution Bundle (manuell).

## Verbotene Aktionen
- Kein echter Device-Write
- Kein sudo/Root-Runner
- Kein echter Deploy
- Keine automatische Ausfuehrung

## Globale Preconditions
- Vollstaendiges Backup
- Lokaler Zugriff
- Nur ein Wegwerfmedium
- Lab Status test_design_ready

## Globale Stop Conditions
- Operator unsicher
- Systemdisk als Ziel
- Verify mismatch
- Audit fehlt

## Globale Evidence Requirements
- lsblk/findmnt/mount vor/nach
- Runner stdout/stderr
- Audit JSONL
- Jobfile Hash
- Snapshot/Fingerprint

## Reihenfolge der Runbooks
1. `RUNBOOK_SUDOERS_RUNTIME_DRYRUN`
2. `RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN`
3. `RUNBOOK_REAL_WRITE_HARDWARE_E2E`
4. `RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E`
5. `RUNBOOK_DEVICE_REENUMERATION`
6. `RUNBOOK_HOTPLUG_UNMOUNT_RACE`
7. `RUNBOOK_ROLLBACK_RUNTIME`

## Runbooks
### RUNBOOK_SUDOERS_RUNTIME_DRYRUN
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_REAL_WRITE_HARDWARE_E2E
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_DEVICE_REENUMERATION
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_HOTPLUG_UNMOUNT_RACE
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_ROLLBACK_RUNTIME
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-closed
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- Rollback/Cleanup: nur erlaubte Testartefakte
