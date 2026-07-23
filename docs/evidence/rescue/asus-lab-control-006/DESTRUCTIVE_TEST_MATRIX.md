# DESTRUCTIVE_TEST_MATRIX

| Test | Ziel | Vorbedingung | Verify | Rollback | Status |
|------|------|--------------|--------|----------|--------|
| Partition Linux-NVMe | Mint layout | exact_match + hash ed84… | GPT/FS | Neuaufbau | plan-only |
| Restore Linux-NVMe | Restore engine | verified backup | Hash/Boot | Re-Restore | plan-only |
| Windows-EFI repair | EFI workflow | EFI backup | BCD/Boot | EFI backup | plan-only |
| Secure-Boot lab | Key mgmt | export pre-state | Boot | restore keys | plan-only |
| Full internal restore | E2E | image verified | Boot+Hash | re-restore | plan-only |

BitLocker mutation: never.
