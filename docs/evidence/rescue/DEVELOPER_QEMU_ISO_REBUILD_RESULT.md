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

## Fazit

Der Developer-QEMU-Rebuild war **profiltechnisch erfolgreich** (Log `profile=developer-qemu`, neues ISO, `console=ttyS0` in ISOLINUX). Die **Autopilot-Enable-Lücke** (Hook 090 / `multi-user.target.wants`) besteht weiter — QEMU Guest Agent Smoke würde erneut `guest_agent_autostart_gap` riskieren.

**Kein Fake-Green:** Rescue bleibt rot/gelb bis QEMU-Smoke mit Agent-Nachweis.

## Nächster Schritt

1. Hook-090-Enable in Chroot nachverfolgen/fixen **oder**
2. QEMU-Smoke mit explizitem Review der Autostart-Lücke (Operator-Entscheidung)

Empfohlen: Autopilot wants-Symlink fixen, ISO-Rebuild, dann Smoke.
