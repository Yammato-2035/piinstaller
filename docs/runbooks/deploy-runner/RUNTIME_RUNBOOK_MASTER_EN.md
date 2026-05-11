# Runtime Runbook Master (EN)

## Purpose
This document bundles all seven manual runtime runbooks. No automatic execution.

## Scope
Runner runtime execution bundle (manual).

## Forbidden Actions
- No real device write
- No sudo/root runner
- No real deploy
- No automatic execution

## Global Preconditions
- Full backup
- Local host access
- Single disposable media
- Lab status test_design_ready

## Global Stop Conditions
- Operator unsure
- System disk as target
- Verify mismatch
- Missing audit

## Global Evidence Requirements
- lsblk/findmnt/mount before/after
- Runner stdout/stderr
- Audit JSONL
- Jobfile hash
- Snapshot/fingerprint

## Runbook Sequence
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
