# PI-RS-BVR-GUI-DCC-001 FAQ (NL)

Stand: **2026-07-21**  
Task: **PI-RS-BVR-GUI-DCC-001**  
Status: **`implemented_pending_physical_retest`**  
Payload-doel: **1.10.1.1**

KB: [GUI_HTTP_SERVER_FAILED_NL.md](../knowledge-base/rescue-stick/GUI_HTTP_SERVER_FAILED_NL.md) · [BVR_STATUS_AND_FALLBACK_NL.md](../knowledge-base/rescue-stick/BVR_STATUS_AND_FALLBACK_NL.md)

---

## 1. Wat is PI-RS-BVR-GUI-DCC-001?

Taak voor GUI HTTP-runtime (ASCII-safe server, readiness vóór Chromium), vier locales voor auto-E2E-voortgangspagina, en DCC-status/drift-zichtbaarheid — zonder wijzigingen aan bevroren BVR-kern (backup/verify/restore).

## 2. Wat is de huidige status?

**`implemented_pending_physical_retest`**: implementatie en unit-tests staan in de workspace; fysieke MSI-retest met payload **1.10.1.1** staat nog open. GUI is **niet** fysiek bevestigd.

## 3. Waarom was de GUI niet zichtbaar bij baseline?

Referentierun `e2e-rescue-msi-20260721-232222-ba58c7a7`: inline Python HTTP-server faalde met `SyntaxError` (non-ASCII in bytes literal) → `http_server_failed`. Chromium startte niet; watchdog viel terug naar TUI.

## 4. Is BVR toch geslaagd?

Ja. Backup, verify, restore, manifest en auto-shutdown **passed**. Overall: **`passed_with_gui_fallback`**.

## 5. Wat is geïmplementeerd als fix?

- Dedicated server `setuphelfer-rescue-ui-http-server` (ASCII-safe)
- Readiness-gate via `GET /health.json`
- Chromium pas na readiness
- Locale-bestanden de/en/fr/nl voor `auto-e2e-progress.html`
- DCC-status en version-drift-matrix

## 6. Gaat BVR door bij GUI-fout?

Ja. BVR-kern en GUI zijn ontkoppeld. GUI-fout blokkeert backup/verify/restore niet.

## 7. Welke payload-versie is het doel?

**1.10.1.1** (baseline **1.10.1.0**). Stick-repack en fysieke test nodig voor groen GUI-licht.

## 8. Welke talen ondersteunt de progress-GUI?

`de-DE`, `en-US`, `fr-FR`, `nl-NL` — via cmdline `setuphelfer_locale=` of omgevingsvariabele.

## 9. Wanneer start Chromium?

Alleen als `/health.json` HTTP **200** geeft, `status=ready`, index bestaat en (progress-pagina) i18n valideert. Alleen open poort is niet genoeg.

## 10. Volgende stap?

Payload **1.10.1.1** bouwen, MSI GE63-retest, evidence importeren naar `physical_msi_result.json`. Zie [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md).

---

## Zie ook

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
