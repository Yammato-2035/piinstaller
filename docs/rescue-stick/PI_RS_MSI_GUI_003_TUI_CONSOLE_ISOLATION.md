# PI-RS-MSI-GUI-003 — TUI Console Isolation (MSI Compat)

## Ausgangslage

- Physischer Retest **PI-RS-MSI-RETEST-002** mit Payload **1.10.0.15** auf MSI GE63: **failed** (TUI zerstört)
- PI-RS-MSI-GUI-002 blockierte `openvt`/`startx`, aber Boot-Progress erzeugte weiter `x11_starting`
- Versionsdrift: ESP **1.10.0.15**, SquashFS-intern `config/version.json` noch **1.10.0.12**

## Ziel

Unter `setuphelfer_msi_compat=1` (mit nomodeset) läuft der Boot **vollständig im stabilen Textmodus**:

- keine Phase `x11_starting`
- keine Meldung „Grafische Oberfläche wird gestartet …“ auf tty1
- kein Überschreiben der Whiptail-TUI durch Boot-Progress
- Session-Evidence pro Boot, keine stale GUI-Logs als aktueller Nachweis

## Implementierung (Payload 1.10.0.16)

| Komponente | Datei / Pfad |
|------------|----------------|
| Zentrales Bootprofil | `backend/core/rescue_msi_boot_profile.py` |
| Boot-Timeline | `backend/core/rescue_boot_timeline.py` |
| Console Ownership | `backend/core/rescue_console_ownership.py` |
| Session-Isolation | `backend/core/rescue_session_evidence.py` |
| Version-Sync | `backend/core/rescue_payload_version_carriers.py` + Repack |
| Boot-Progress (Shell) | `scripts/rescue-live/image/setuphelfer-rescue-boot-progress` |
| Common / TUI | `setuphelfer-rescue-common.sh`, `setuphelfer-rescue-tui.sh` |

### MSI-Compat-Bootprofil (Beispiel)

```json
{
  "boot_mode": "tui_only",
  "gui_available": false,
  "gui_progress_allowed": false,
  "reason_code": "msi_compat_nomodeset",
  "operator_mode": "stable_tui"
}
```

### Timeline unter MSI-Compat

- **Ersetzt:** `x11_starting` → **`tui_mode_selected`**
- **Meldung:** „MSI-Kompatibilitätsmodus: Textoberfläche wird verwendet.“
- **Audit:** `gui_skipped` (nur JSONL, kein tty1-Render)

## Payload 1.10.0.16

| Feld | Wert |
|------|------|
| Artefakt | `build/rescue/filesystem.squashfs.repacked-1.10.0.16` |
| SHA256 | `cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5` |
| Versionsträger | `VERSION`, `config/rescue_payload_version.json`, `config/version.json` — alle **1.10.0.16** |
| USB-Write | **nicht durchgeführt** in diesem Sprint |

## Tests & Gates

```bash
PYTHONPATH=backend python3 -m pytest -q \
  backend/tests/test_rescue_payload_msi_gui003_tui_console_isolation.py

./scripts/check-rescue-payload-msi-gui003-content.sh
./scripts/check-rescue-payload-no-secrets.sh build/rescue/filesystem.squashfs.repacked-1.10.0.16
```

## Abnahme

**passed** — physischer GE63-Retest via PI-RS-MSI-AUTO-EVIDENCE-001 (Payload **1.10.0.20**, Session `20260713_003100_boot`).

## Nächster Schritt

Optional: PI-RS-TEL-LIVE-001 / Telemetry-Send nach expliziter Freigabe.

## Siehe auch

- [PI_RS_MSI_AUTO_EVIDENCE_001.md](PI_RS_MSI_AUTO_EVIDENCE_001.md)

- [PI_RS_MSI_GUI_002_DISABLE_GUI_UNDER_MSI_COMPAT.md](PI_RS_MSI_GUI_002_DISABLE_GUI_UNDER_MSI_COMPAT.md)
- [PI_RS_MSI_GUI_003_FAQ.de.md](../faq/PI_RS_MSI_GUI_003_FAQ.de.md)
- [MSI_TUI_CONSOLE_ISOLATION_KB_DE.md](../knowledge-base/rescue/MSI_TUI_CONSOLE_ISOLATION_KB_DE.md)
- Evidence: `docs/evidence/pi_rs_msi_gui_003/`
