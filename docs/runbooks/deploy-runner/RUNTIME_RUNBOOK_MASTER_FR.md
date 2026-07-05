> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/deploy-runner/RUNTIME_RUNBOOK_MASTER_EN.md`). Bitte bei Release manuell gegenlesen.

# Runtime Runbook Master (EN)

## Purpose
This document bundles all seven manual runtime runbooks. Non automatic execution.

## Scope
Runner runtime execution bundle (manual).

## Forbidden Actions
- Non real Périphérique write
- Non sudo/root runner
- Non real Déploiement
- Non automatic execution

## Global Preconditions
- Full Retourup
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
5. `RUNBOOK_Périphérique_REENUMERATION`
6. `RUNBOOK_HOTPLUG_UNMOUNT_RACE`
7. `RUNBOOK_ROLLRetour_RUNTIME`

## Runbooks
### RUNBOOK_SUDOERS_RUNTIME_DRYRUN
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_REAL_WRITE_HARDWARE_E2E
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_Périphérique_REENUMERATION
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_HOTPLUG_UNMOUNT_RACE
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte

### RUNBOOK_ROLLRetour_RUNTIME
- Ziel: manueller kontrollierter Lauf
- Inputs: vorherige Nachweise/Reports
- Manuelle Schritte: strikt sequenziell
- Erwartete Evidence: JSONL/Hashes/State-Dumps
- Stop Conditions: fail-Fermerd
- Pass Criteria: definierte Sicherheitsziele erreicht
- Fail Criteria: jede harte Abweichung
- RollRetour/Cleanup: nur erlaubte Testartefakte
