# FAQ PI-RS-ASUS-PHYSICAL-DIAG-003 (FR)

1. **Warum wird noch nichts auf die NVMe geschrieben?** Nur Diagnose; `write_allowed=false`.
2. **Was sind EUI und NGUID?** Stabile Namespace-IDs der NVMe (Hardware).
3. **Warum reicht `/dev/nvme0n1` nicht?** Gerätenamen wechseln zwischen Boots.
4. **Was sagt SMART?** Health-Hinweis; schließt RAM/Firmware/Treiber nicht aus.
5. **NVMe-Error-Log?** Controller-Ereignisse; alt ≠ aktuell kritisch.
6. **Wo sucht Setuphelfer Logs?** Panther/Rollback und bekannte Setup-Pfade (read-only).
7. **Keine Panther-Logs?** Kein Beweis für fehlerfreies Setup → Retest mit Log-Sammlung.
8. **Ist BIOS 335 zwingend?** Empfehlung/plausibel, kein bewiesener Root Cause.
9. **Wann Zielrollen?** Nach stabiler Identity; weiterhin ohne Schreibfreigabe.
10. **Wann Schreibfreigabe?** Erst nach explizitem späteren Auftrag/Gate.
