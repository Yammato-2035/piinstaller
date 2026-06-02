# Developer QEMU ISO Rebuild — Result

**Datum:** 2026-06-03  
**Ingest-Lauf:** Verify only (kein Build, kein QEMU)

## Ergebnis

| Aspekt | Status |
|--------|--------|
| Build LB_EXIT=0 | **yes** |
| Profil developer-qemu verifiziert | **yes** |
| ISO + SHA256 | **yes** |
| Serial Bootappend in ISO | **yes** |
| Autopilot-Unit in Squashfs | **yes** |
| Autopilot enabled/wanted | **no** |
| Verify-Status | **review_required** |

## Fazit (historisch ISO `3ee02b36…`)

Der Developer-QEMU-Rebuild war **profiltechnisch erfolgreich** (Log `profile=developer-qemu`, neues ISO, `console=ttyS0` in ISOLINUX). Die **Autopilot-Enable-Lücke** (Hook 090 / `multi-user.target.wants`) bestand in diesem ISO.

**Fix (2026-06-03):** Statischer wants-Symlink — `DEVELOPER_QEMU_AUTOPILOT_ENABLE_FIX_RESULT.md`. **ISO-Rebuild erforderlich**; dieser Verify-Stand bleibt `review_required` bis ersetzt.

## Nächster Schritt

1. Operator: `sudo clean` → Prepare (developer-qemu) → Build `--profile developer-qemu`
2. Squashfs-Validator Exit 0 (inkl. Autopilot-wants)
3. QEMU Guest Agent Smoke Operator Run, NO USB
