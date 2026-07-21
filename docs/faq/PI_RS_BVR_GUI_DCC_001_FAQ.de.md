# PI-RS-BVR-GUI-DCC-001 FAQ (DE)

Stand: **2026-07-21**  
Task: **PI-RS-BVR-GUI-DCC-001**  
Status: **`implemented_pending_physical_retest`**  
Payload-Ziel: **1.10.1.1**

KB: [GUI_HTTP_SERVER_FAILED_DE.md](../knowledge-base/rescue-stick/GUI_HTTP_SERVER_FAILED_DE.md) · [BVR_STATUS_AND_FALLBACK_DE.md](../knowledge-base/rescue-stick/BVR_STATUS_AND_FALLBACK_DE.md)

---

## 1. Was ist PI-RS-BVR-GUI-DCC-001?

Auftrag zur GUI-HTTP-Runtime (ASCII-safe Server, Readiness vor Chromium), vier Locales für die Auto-E2E-Fortschrittsseite, DCC-Status/Drift-Sichtbarkeit — ohne Änderungen am eingefrorenen BVR-Kern (Backup/Verify/Restore).

## 2. Welcher Status gilt aktuell?

**`implemented_pending_physical_retest`**: Implementierung und Unit-Tests sind im Workspace; ein physischer MSI-Nachtest mit Payload **1.10.1.1** steht noch aus. Die GUI gilt **nicht** als physisch bestätigt.

## 3. Warum war die GUI beim Baseline-Lauf nicht sichtbar?

Referenzlauf `e2e-rescue-msi-20260721-232222-ba58c7a7`: Der inline-Python-HTTP-Server scheiterte mit `SyntaxError` (non-ASCII in bytes literal) → `http_server_failed`. Chromium startete nicht; Watchdog fiel auf TUI zurück.

## 4. Lief BVR trotzdem erfolgreich?

Ja. Backup, Verify, Restore, Manifest und Auto-Shutdown **passed**. Gesamtstatus: **`passed_with_gui_fallback`**.

## 5. Was wurde zur Behebung implementiert?

- Dedizierter Server `setuphelfer-rescue-ui-http-server` (ASCII-safe)
- Readiness-Gate über `GET /health.json` (HTTP 200 + Payload/Entry/Locale)
- Chromium erst nach Readiness
- Locale-Dateien de/en/fr/nl für `auto-e2e-progress.html`
- DCC-Status via `rescue_bvr_dcc_status.py` und Version-Drift-Matrix

## 6. Läuft BVR weiter, wenn die GUI ausfällt?

Ja. BVR-Kern und GUI sind entkoppelt. GUI-Fehler blockieren Backup/Verify/Restore nicht.

## 7. Welche Payload-Version ist das Ziel?

**1.10.1.1** (Baseline hatte **1.10.1.0**). Stick-Repack und physischer Test sind Voraussetzung für grüne GUI-Ampel.

## 8. Welche Sprachen unterstützt die Progress-GUI?

`de-DE`, `en-US`, `fr-FR`, `nl-NL` — Auswahl via Cmdline `setuphelfer_locale=` oder Umgebungsvariable.

## 9. Wann startet Chromium?

Erst wenn `/health.json` HTTP **200** liefert, `status=ready`, Index existiert und (für Progress-Page) i18n validiert ist. Ein offener Port allein reicht nicht.

## 10. Was ist der nächste Schritt?

Payload **1.10.1.1** bauen, MSI GE63-Nachtest durchführen, Evidence nach `physical_msi_result.json` importieren. Siehe [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md).

---

## Siehe auch

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [docs/evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md](../evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md)
