# Phase 0 — Workspace / Branch / Strategy (007)

**Campaign:** PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007  
**Stand:** 2026-08-08

```
============================================================
WORKSPACE
============================================================
Aktueller Workspace: /home/volker/piinstaller-asus-emergency-linux-telemetry-003
Branch:              pi-rs-asus-autonomous-diag-install-007
Base HEAD:           f413ff68
Zweck:               PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007
Erwartetes Repository: piinstaller (origin Yammato-2035/piinstaller)
============================================================
```

| Feld | Wert |
|---|---|
| pwd / toplevel | `/home/volker/piinstaller-asus-emergency-linux-telemetry-003` |
| Branch | `pi-rs-asus-autonomous-diag-install-007` |
| Base HEAD | `f413ff68` (`f413ff687073e269bf17ac5586e096934f75d59c`) |
| Vorgänger-Evidence | `docs/evidence/rescue/asus-rootcause-006/` |
| Neue Evidence | `docs/evidence/rescue/asus-autonomous-007/` |
| Stick payload (carrier) | **1.10.5.0** — unverändert bis Carrier-Update |
| Strategiewechsel | **High-info boot** ersetzt Single-Hypothesis-Boot-Juggling |

## Strategy change

Statt mehrerer Einzelhypothesen-Boots (Profil A → B → C mit manueller Umschaltung) gilt für 007:

- Ein **ASUS-TUI-BASELINE-HIGHINFO**-Boot sammelt maximale Diagnostik auf stabilem TUI-Baseline.
- Kein GUI/Chromium-Autostart; Xorg-Probe nur controlled/isolated (`setuphelfer_xorg_probe=1`).
- Parallel-Agenten planen Fixes/Install-Pfade auf Basis dieser High-Info-Evidenz, nicht durch wiederholtes Profil-Wechseln am Stick.

## Safety constraints (Phase 0)

- **Kein interner NVMe-Write** ohne Freigabe.
- **Kein Install** ohne **doppelte Operator-Bestätigung** (dual operator confirm).
- Stick bleibt auf Carrier **1.10.5.0**, bis ein explizites Carrier-Update beauftragt und verifiziert ist.

## Edit scope (dieser Auftrag)

1. `backend/rescue/asus_boot_profiles.py` — Profil `ASUS-TUI-BASELINE-HIGHINFO`
2. Evidence unter `docs/evidence/rescue/asus-autonomous-007/` (Phase0, Parallel-Plan, Agent-Results-Stub)
