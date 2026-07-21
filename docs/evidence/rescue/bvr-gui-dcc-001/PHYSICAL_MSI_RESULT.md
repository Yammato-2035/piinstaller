# Physical MSI Result – PI-RS-BVR-GUI-DCC-001

**Status: `passed_with_gui_fallback`**

| Feld | Wert |
|------|------|
| Run-ID | `e2e-rescue-msi-20260722-002744-a8f0a50d` |
| Payload | **1.10.1.1** |
| Backup | passed (166 Dateien, ~130 MB) |
| Verify | passed |
| Restore | passed |
| Manifest | match |
| Auto-Shutdown | ja |
| HTTP-Server | **ready** (`/health.json` 200, Locales ok) |
| GUI sichtbar | **nein** (Operator) |
| Watchdog | `openvt_console_2_not_released` → TUI-Fallback |
| TUI-Anzeige | inkonsistent (bis 11., springt, läuft unten raus) |

## Bewertung

- BVR-Kern erneut grün.
- HTTP-Root-Cause aus Baseline ist auf Hardware behoben.
- Grafische Oberfläche für den Operator **nicht** sichtbar → Auftrag **nicht** vollständig `passed`.
- Nächster Fokus: VT/openvt/Chromium-Sichtbarkeit + stabile TUI-Fortschrittsanzeige.
