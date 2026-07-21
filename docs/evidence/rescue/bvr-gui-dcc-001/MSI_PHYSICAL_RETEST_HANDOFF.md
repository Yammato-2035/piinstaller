# MSI Physical Retest Handoff – PI-RS-BVR-GUI-DCC-001

**Status:** `implemented_pending_physical_retest`  
**Payload on stick:** **1.10.1.1**  
**SHA256:** `2c0a1552831219e399c7496c353bbf343d13eb0a5e042b1293639d22e22fbbb2`  
**Feature commit:** `4098f004`

## Operator steps

1. Stick (`Ultra Line` / SETUPHELFER + SETUP_LOGS) in MSI GE63 stecken.
2. SABRENT-BVR-Zielplatte anschließen (nicht System-NVMe).
3. Vom Stick booten (GUI Physical E2E default / auto).
4. Erwarten: grafische Progress-Seite sichtbar, Sprache de-DE, **kein** Watchdog-Fallback.
5. Unattended Backup → Verify → Restore → Manifest → Evidence → Auto-Shutdown.
6. Stick zurück; Evidence von SETUP_LOGS importieren.

## Pass criteria

- GUI sichtbar, HTTP ready, kein Fallback
- BVR-Kern passed
- Overall: `passed` (nicht `passed_with_gui_fallback`)
