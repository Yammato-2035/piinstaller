# PI-RS-BVR-GUI-DCC-001 FAQ (EN)

As of: **2026-07-21**  
Task: **PI-RS-BVR-GUI-DCC-001**  
Status: **`implemented_pending_physical_retest`**  
Payload target: **1.10.1.1**

KB: [GUI_HTTP_SERVER_FAILED_EN.md](../knowledge-base/rescue-stick/GUI_HTTP_SERVER_FAILED_EN.md) · [BVR_STATUS_AND_FALLBACK_EN.md](../knowledge-base/rescue-stick/BVR_STATUS_AND_FALLBACK_EN.md)

---

## 1. What is PI-RS-BVR-GUI-DCC-001?

Task for GUI HTTP runtime (ASCII-safe server, readiness before Chromium), four locales for the auto-E2E progress page, and DCC status/drift visibility — without changing the frozen BVR core (backup/verify/restore).

## 2. What is the current status?

**`implemented_pending_physical_retest`**: Implementation and unit tests are in the workspace; a physical MSI retest with payload **1.10.1.1** is still pending. The GUI is **not** physically confirmed yet.

## 3. Why was the GUI not visible on the baseline run?

Reference run `e2e-rescue-msi-20260721-232222-ba58c7a7`: the inline Python HTTP server failed with `SyntaxError` (non-ASCII in bytes literal) → `http_server_failed`. Chromium did not start; watchdog fell back to TUI.

## 4. Did BVR still succeed?

Yes. Backup, verify, restore, manifest, and auto-shutdown **passed**. Overall status: **`passed_with_gui_fallback`**.

## 5. What was implemented to fix it?

- Dedicated server `setuphelfer-rescue-ui-http-server` (ASCII-safe)
- Readiness gate via `GET /health.json` (HTTP 200 + payload/entry/locale)
- Chromium only after readiness
- Locale files de/en/fr/nl for `auto-e2e-progress.html`
- DCC status via `rescue_bvr_dcc_status.py` and version drift matrix

## 6. Does BVR continue when the GUI fails?

Yes. BVR core and GUI are decoupled. GUI failure does not block backup/verify/restore.

## 7. What is the target payload version?

**1.10.1.1** (baseline used **1.10.1.0**). Stick repack and physical test are required for a green GUI traffic light.

## 8. Which languages does the progress GUI support?

`de-DE`, `en-US`, `fr-FR`, `nl-NL` — selected via cmdline `setuphelfer_locale=` or environment variable.

## 9. When does Chromium start?

Only when `/health.json` returns HTTP **200**, `status=ready`, index exists, and (for progress page) i18n validates. An open port alone is not enough.

## 10. What is the next step?

Build payload **1.10.1.1**, run MSI GE63 retest, import evidence to `physical_msi_result.json`. See [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md).

---

## See also

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [docs/evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md](../evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md)
