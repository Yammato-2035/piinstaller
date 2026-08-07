# PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — Interim Implementation Status

**Stand:** 2026-08-07  
**Branch:** `pi-rs-asus-rootcause-telemetry-006`  
**Ausgangs-HEAD:** `b425097ba06b8a889ab95a2feb1ebcf5525ff7fa`  
**Verdict jetzt:** `carrier_update_verified` + `insufficient_evidence` / **kein** `asus_tui_baseline_stable` (Stick 1.10.3.0 geschrieben; physischer TUI-Baseline-Boot ausstehend)

## Erledigt (Workspace)

| Phase | Status |
|---|---|
| 0 Workspace/Carrier | dokumentiert |
| 1 Handover Reconciliation | `ASUS_02_HANDOVER_RECONCILIATION.md` |
| 2 TUI-First Profile | `ASUS-TUI-BASELINE`, `ASUS-XORG-FORENSIC`, `ASUS-GUI-CONTROLLED` |
| 2 Entrypoint | kein GUI-Autostart bei TUI-Baseline; Xorg-Forensic isoliert |
| 3 Console Ownership | `fallback_tui` / `unknown`; Restore → `fallback_tui` |
| 4 Diagnostics-Timer | Condition gegen tui_baseline/xorg_forensic; 3min/10min; Entrypoint stoppt Timer |
| 5 Port-Ownership | `backend/core/rescue_port_ownership.py` |
| 7 Chromium-Gate | `graphical_browser_start_allowed` in ui-launch |
| 8–12 startx Forensic | `setuphelfer-rescue-startx-forensic.sh` + Taxonomy-Modul |
| GRUB Default | `set default=0` → **ASUS-TUI-BASELINE** |
| Tests | `test_pi_rs_asus_rootcause_006_v1.py` + angepasste FAT32/Version-Tests |

## Noch offen (bewusst)

- Physische Boots 1–2× ASUS-TUI-BASELINE (Operator)
- Volle GPU/cmdline/blacklist Sentinels-Anbindung an Telemetrie-Events
- Telemetry-Server Case-Loop End-to-End
- Dashboard/i18n-Vollausbau

## Nächster physischer Ablauf (Operator)

1. ~~Workspace-Fix auf Stick~~ → `carrier_update_verified` (SquashFS `4629ca61…`, GRUB `15497518…`, Payload 1.10.3.0).
2. **BOOT 1:** Menü **ASUS-TUI-BASELINE** (Default) — erwarten: TUI, kein Chromium, kein startx, `console_owner=tui_owned`.
3. Stick zurück → Evidence prüfen.
4. **BOOT 2:** gleiche Baseline wiederholen.
5. Erst dann **ASUS-XORG-FORENSIC** (kein Chromium).

## Fake-Green-Regel

Kein Claim `asus_fixed` / `production_ready` / `gui_ready` ohne physischen Nachweis.
