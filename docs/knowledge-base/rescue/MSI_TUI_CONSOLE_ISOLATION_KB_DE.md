# MSI TUI & Console Isolation (PI-RS-MSI-GUI-003)

**Stand:** 2026-07-13  
**Payload:** 1.10.0.20  
**Status:** **passed** (physischer Retest abgeschlossen)

## Kontext

| Sprint | Ergebnis |
|--------|----------|
| PI-RS-MSI-FIX-001 | Console-Shield, weniger tty1-Clears |
| PI-RS-MSI-GUI-002 | GUI unter MSI-Compat gesperrt (`openvt`/`startx` blockiert) |
| PI-RS-MSI-RETEST-002 | **failed** — TUI zerstört, `x11_starting` in Timeline |
| **PI-RS-MSI-GUI-003** | Boot-Progress + tty1-Isolation + Session-Evidence |

**Testhardware:** MSI GE63 Raider RGB 8RF, Modell MS-16P5.

## Root Cause (bestätigt / stark belegt)

1. **Boot-Progress** (`setuphelfer-rescue-boot-progress`) nutzte feste Phasenliste mit `x11_starting`, unabhängig von `gui-availability.json`.
2. **tty1-Konflikt:** Boot-Progress-Service und Whiptail-TUI laufen parallel auf `/dev/tty1`.
3. **Console-Shield v1** kannte `tty1_clear_allowed`, aber kein explizites **`tty1_write_allowed`** nach TUI-Übergabe.
4. **Stale Evidence:** `gui-start.log` / `rescue-ui-status.json` ohne Session-Bindung → alte Session `20260712_015909` in neuer Boot-Evidence.
5. **Versionsdrift:** Repack schrieb `VERSION`/`rescue_payload_version.json`, nicht `config/version.json` → `/api/version` meldete 1.10.0.12 bei ESP 1.10.0.15.

## Architektur (1.10.0.16)

```text
cmdline (msi_compat=1, nomodeset)
    → resolve_rescue_boot_profile() → boot_mode=tui_only
    → plan_boot_progress_steps() → tui_mode_selected (kein x11_starting)
    → init_boot_session() → session_id, boot_id
    → transition_console_owner(boot_progress → tui_owned)
    → mirror_evidence_file() mit stale-Guard
```

### Zentrale Module

| Modul | Rolle |
|-------|--------|
| `rescue_msi_boot_profile.py` | `gui_progress_allowed`, `boot_mode` |
| `rescue_boot_timeline.py` | Phasenplanung, JSONL, `simulate` |
| `rescue_console_ownership.py` | tty1-Besitz, Audit `RESCUE_CONSOLE_WRITE_BLOCKED_TUI_OWNED` |
| `rescue_session_evidence.py` | Session-Init, Stale-Erkennung |
| `rescue_payload_version_carriers.py` | Konsistente Versionsträger im Repack |

### MSI-Compat-Zielablauf tty1

```text
boot_progress → tui_initializing → tui_owned → shutdown
```

**Nicht erlaubt:** `tui_owned` → Boot-Progress schreibt erneut auf tty1.

## Operator: Retest — **passed** (2026-07-13)

Session **`20260713_003100_boot`**, Payload **1.10.0.20**, via PI-RS-MSI-AUTO-EVIDENCE-001:

1. Unattended GRUB-Boot (MSI-Lab-Modus)
2. Late-Evidence bei **153,8 s** Uptime
3. `lab-auto-result.json`: **passed**
4. Shutdown: `auto_shutdown_evidence_complete`

Manuelle Retest-Checkliste (003) ist durch Auto-Lab superseded. Referenz: [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)

## Operator: Retest-Checkliste (PI-RS-MSI-RETEST-003) — historisch

1. Stick via **PI-RS-USB-UPDATER-001** auf 1.10.0.16
2. ESP-`version.json` und SquashFS-intern prüfen (alle **1.10.0.16**)
3. GE63 booten mit MSI-Compat-GRUB-Eintrag
4. TUI **≥2 Min** nutzbar (Menü, Navigation)
5. `boot-timeline.jsonl`: **kein** `x11_starting`
6. `gui-availability.json`: `session_id` = aktuelle Boot-Session
7. Kein `openvt` / kein Xorg-Log in aktueller Session

## Evidence-Pfade (nach Boot)

```text
SETUP_LOGS/setuphelfer/evidence/msi-rs011b/boot-timeline.jsonl
SETUP_LOGS/setuphelfer/evidence/boot/gui-availability.json
SETUP_LOGS/setuphelfer/evidence/boot/console-shield.json
SETUP_LOGS/setuphelfer/logs/boot/gui-start.log
```

Import-Beispiel:

```bash
cp -a /media/.../SETUP_LOGS/setuphelfer/evidence \
  docs/evidence/pi_rs_msi_retest_003/msi_session/
```

## Gates (Entwicklung)

```bash
./scripts/check-rescue-payload-msi-gui003-content.sh
./scripts/check-rescue-payload-no-secrets.sh build/rescue/filesystem.squashfs.repacked-1.10.0.16
```

## Verweise

- FAQ: [PI_RS_MSI_GUI_003_FAQ.de.md](../../faq/PI_RS_MSI_GUI_003_FAQ.de.md)
- Auto-Lab: [MSI_LAB_AUTO_EVIDENCE_KB_DE.md](MSI_LAB_AUTO_EVIDENCE_KB_DE.md), [PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md](../../evidence/pi_rs_msi_auto_evidence_001/PI_RS_MSI_AUTO_EVIDENCE_001_SUMMARY.md)
- Runbook: [PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md](../../rescue-stick/PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md)
- Evidence: `docs/evidence/pi_rs_msi_gui_003/`, `docs/evidence/pi_rs_msi_auto_evidence_001/`
- i18n (Rescue UI): `frontend/src/rescue/i18n/*.json` → `boot.msiCompat.*`, `boot.msiLabAuto.*`
