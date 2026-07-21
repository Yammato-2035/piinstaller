# BVR Automation (Rescue Stick)

**PI-RS-BVR-GUI-DCC-001:** BVR-Kern (Backup/Verify/Restore/Evidence/Auto-Shutdown) ist **eingefroren** und unabhängig von der GUI-Schicht.

## Automatischer MSI-E2E-Lauf

Bei `setuphelfer_msi_e2e_auto=1`:

1. Geräteerkennung und SABRENT-Ziel
2. Backup → Verify → Restore
3. Manifest-Vergleich
4. Evidence auf SETUP_LOGS
5. Auto-Shutdown

Der BVR-Kern lief im Baseline-Lauf (`e2e-rescue-msi-20260721-232222-ba58c7a7`) **passed** — auch als die GUI wegen `http_server_failed` ausfiel.

## GUI-Schicht (DCC-001)

Die Fortschrittsanzeige (`auto-e2e-progress.html`) benötigt einen lokalen HTTP-Server:

- **Fix:** dedizierter ASCII-safe Server — siehe [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- **Baseline-Ursache:** inline Python mit non-ASCII in bytes literal → `SyntaxError` → `http_server_failed`
- **Status:** implementiert, physischer MSI-Nachtest ausstehend

## Eingefrorene BVR-Dateien

Siehe [BVR_CORE_FREEZE_PI_RS_BVR_GUI_DCC_001.md](../architecture/BVR_CORE_FREEZE_PI_RS_BVR_GUI_DCC_001.md).

## Siehe auch

- [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md)
- [docs/evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
