# PLANNING_MATRIX — PI-RS-ASUS-AUTOCAPTURE-BIOS-007

## Critical path

Autonomous full-lab-capture + Windows live-capture preparation on G513QM, then auto-import on stick return. BIOS config changes remain **capability-gated**, one change per run. BIOS 335 is a separate firmware-change run (not required by missing Panther alone).

## Matrix

| Bereich | Ist-Stand | Ziel | Automatisierbar | Risiko | Gate | Rollback |
|---------|-----------|------|-----------------|--------|------|----------|
| Identity | Lab-YAML + Auth | Bootzeit exact_match | ja | kritisch | manufacturer+G513QM+machine_id+uuid | keine Mutation |
| Run-ID | teilweise / hw-discovery | immer `asus-*` Schema | ja | hoch | validate_run_id | Lauf blockieren |
| Hardware-Capture | Discovery-Engine | maximal baseline + Manifest | ja | niedrig | Speicherplatz | Teilcapture |
| Windows-Capture | fehlt physisch live | auto prepare + wrapper | ja | hoch | SETUP_LOGS ready | Offline-Fallback |
| Import | manuell | `import-asus-lab-runs` | ja | mittel | Identity/Run-ID/Secret | Quarantäne |
| BIOS-State | teilweise | capability inventory | überwiegend | mittel | read-only | keiner |
| BIOS-Change | plan-only | contract + UI checklist | teilweise | kritisch | Pre/Post/Rollback | restore setting |
| Secure Boot | plan-only | inventory + UI | teilweise | kritisch | Key-Backup meta | UI restore |
| Disk/EFI | freigegeben | later fingerprint | ja | kritisch | confirmed roles | Restore |
| BitLocker | RO | unverändert | ja | kritisch | mutation guard | blockieren |
| Carrier versions | Plaintext konnte stale | alle Carrier equal | ja | hoch | consistency gate | Build block |

## Self-identified failure modes (≥10)

1. Carrier plaintext ≠ JSON → Build/Stick block
2. WIN_DIAG nesting on inject → rm -rf before copy
3. Wrong machine (MSI) → identity block
4. SETUP_LOGS full → orchestrator abort
5. Collector writes to NVMe → SETUP_LOGS label only
6. Secret in evidence → quarantine
7. Duplicate import → already_imported
8. Reboot loses run_id → persist AUTO_IMPORT.READY + queue marker
9. BIOS write invented → write_supported false + UI checklist only
10. BitLocker recovery after SB change → bitlocker_recovery_risk mandatory
11. Legacy hw-discovery flood on auto-import → include_legacy_hw default false
12. Claiming Setup root cause from insufficient_evidence → forbidden in finalize

## plan_status

```text
plan_status: ready
```
