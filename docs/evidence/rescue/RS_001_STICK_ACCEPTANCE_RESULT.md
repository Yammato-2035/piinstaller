# RS-001 Stick Acceptance — Ergebnis

**Datum:** 2026-06-10  
**HEAD:** `d5042e4` → Fix `1.7.11.0`  
**Stick:** `/dev/sdb1` (SETUPHELFER)  
**Expected SquashFS:** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc`

---

## Summary

| Feld | Wert |
|------|------|
| `acceptance_status` | **review_required** |
| `exit_code` | **20** |
| `hardware_retest_allowed` | **false** |
| `rs001_status` | **yellow** |

---

## Levels

| Level | Status |
|-------|--------|
| 1 FAT32/Hash | **ok** |
| 2 SquashFS Content | **ok** (Version `1.7.10.1` im SquashFS) |
| 3 Launcher/Fallback/Network | **review_required** |
| 4 GRUB Branding | **review_required** |
| 5 QEMU Menu Smoke | **not_run** |

---

## Blocker (vor Hardware-Retest)

### Level 4 — GRUB Branding

- Kein `boot/grub/themes/setuphelfer/` auf ESP
- `grub.cfg` ohne Theme/gfx-Module
- BOOTX64 ohne gfx-Module in `evidence.json`

### Level 3 — SquashFS Contracts (Stick vs. Workspace)

Stick-SquashFS `1.7.10.1` **ohne** Fixes aus `1.7.10.2`:

- Kein `setuphelfer_rescue_run_network_interactive` → **Netzwerk-Crash auf Hardware erklärt**
- Kein `set +e` / `return_to_menu` im Network-Skript auf Stick
- Kein sicheres Notmenü-UX (Status-Kurzfassung, sicherer Notmodus-Text)

**Workspace `1.7.11.0`:** Contract **ok** — Warnung: `workspace_passes_contract_but_stick_squashfs_outdated_rebuild_required`

---

## Stick-Logs Untersuchung

| Pfad auf ESP (Host-Readback) | Vorhanden |
|------------------------------|-----------|
| `setuphelfer/logs/` | **nein** |
| `setuphelfer/evidence/boot/` | **nein** |
| `setuphelfer/rescue/evidence.json` | ja (Writer-Metadaten) |

**Fazit:** Operator-Log-Export auf Hardware hat **keine persistierten Logs** auf der ESP hinterlassen (nur Writer-Metadaten). Fehlerdiagnose daher aus SquashFS-Inhalt + Hardware-Befund:

1. Netzwerk-Crash = alter Launcher/Common ohne crash-safe Wrapper
2. GRUB ohne Logo = Theme nie auf ESP (unabhängig von Logs)
3. React fehlt = kein Browser im SquashFS (Contract, kein Log-Thema)

Evidence JSON: `docs/evidence/runtime-results/rescue/rs001_stick_acceptance_latest.json`

---

## Nächster Schritt

1. SquashFS-Rebuild mit `1.7.11.0` (enthält 1.7.10.2-Fixes + Acceptance-Layer)
2. GRUB-Theme + `grub.cfg` auf ESP aktualisieren
3. `check-rs001-stick-acceptance.sh` → `acceptance_status=ok`
4. Dann Hardware-Retest (Level 6)
