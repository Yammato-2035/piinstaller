# RS-001 Stick Acceptance — Ergebnis

**Datum:** 2026-06-10  
**HEAD:** `01ffba3`  
**Version:** `1.7.11.0`  
**Stick:** `/dev/sdb1` (SETUPHELFER, Ultra Line)  
**Expected SquashFS SHA256:** `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d`

---

## Summary

| Feld | Wert |
|------|------|
| `acceptance_status` | **ok** |
| `exit_code` | **0** |
| `hardware_retest_allowed` | **true** |
| `rs001_status` | **yellow** (Hardware-Retest Level 6 ausstehend) |

---

## Levels

| Level | Status |
|-------|--------|
| 1 FAT32/Hash | **ok** |
| 2 SquashFS Content | **ok** (Version `1.7.11.0` im SquashFS) |
| 3 Launcher/Fallback/Network | **ok** |
| 4 GRUB Branding | **ok** |
| 5 QEMU Menu Smoke | **not_run** |

---

## Materialization

| Schritt | Status |
|---------|--------|
| React UI Build | success (`1.7.11.0`, offline_first) |
| SquashFS Repack | success (NEW ≠ OLD) |
| Payload Update | success (udisksctl rw — sudo mount nicht verfügbar) |
| GRUB Branding Update | success (`update-fat32-esp-grub-branding.sh`) |
| Verify Hash Gate | success |
| Stick Acceptance | **ok** |

**Alter Stick-SHA256:** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` (1.7.10.1)  
**Neuer SquashFS-SHA256:** `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d` (1.7.11.0)

---

## Warnungen

- `no_operator_logs_on_stick_esp_readback` — erwartet bis Hardware-Retest
- Payload-Update-Skript: `--execute-update` blockiert ohne passwordless sudo; Operator-Fallback über udisksctl rw dokumentiert

---

## Nächster Schritt

**Hardware-Retest Level 6** auf Referenzhardware (MSI) — **Operator ausstehend** (2026-06-10 Agent-Lauf: Phase 0 ok, Phase 1 nicht ausführbar). RS-001 bleibt yellow bis erfolgreicher Operator-Befund.

Evidence JSON: `docs/evidence/runtime-results/rescue/rs001_stick_acceptance_latest.json`  
Level-6 USB readback: `docs/evidence/runtime-results/rescue/rs001_level6_hardware_retest_from_usb/`
