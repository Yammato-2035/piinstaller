# PLAN_SELF_REVIEW — PI-RS-ASUS-AUTOCAPTURE-BIOS-007

## Adversarial checks

| Risiko | Gegenmaßnahme |
|--------|---------------|
| MSI statt ASUS | exact_match Auth; MSI manufacturer mismatch |
| nvme0/1 Drift | Fingerprints in YAML; destructive still requires confirmed |
| Stick als Zielplatte | SETUP_LOGS label + denylist |
| Stale carriers | evaluate_carrier_consistency inkl. Plaintext |
| Auto-Import aller Altläufe | Queue/AUTO_IMPORT.READY; legacy opt-in |
| Secret commit | redaction_gate blocked/quarantine |
| Fake Setup-Ursache | finalize setzt definitive_freeze_root_cause_known=false |
| Undokumentierter NVRAM-Write | write_supported=false → firmware UI checklist |
| BitLocker indirekt | bitlocker_recovery_risk Pflicht bei SB/TPM |
| Parallel Discovery-Engine | reuse rescue_hardware_discovery_*; asus_lab orchestriert nur |

## plan_status

```text
plan_status: ready
```
