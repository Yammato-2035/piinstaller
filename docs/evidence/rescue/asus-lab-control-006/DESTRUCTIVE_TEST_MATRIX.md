# DESTRUCTIVE_TEST_MATRIX

| Test | Ziel | Vorbedingung | Verify | Rollback | Status diesmal |
|------|------|--------------|--------|----------|----------------|
| Partitionierung Linux-NVMe | Mint-Lab-Layout | exact identity + hash `ed84…` + confirmed | GPT/FS | Neuaufbau | plan-only |
| Restore auf Linux-NVMe | Restore-Engine | Backup verifiziert | Hash/Boot | Re-Restore | plan-only |
| Windows-EFI-Reparatur | EFI-Workflow | EFI-Backup | BCD/Boot | EFI-Backup | plan-only |
| Secure-Boot-Lab | Key-Management | Export Pre-State | Bootprüfung | Restore Keys | plan-only |
| kompletter interner Restore | Recovery-E2E | belastbares Image | Boot + Hash | erneuter Restore | plan-only |

Keine destruktive Mutation in dieser Session ausgeführt.
BitLocker-Mutation: verboten.
