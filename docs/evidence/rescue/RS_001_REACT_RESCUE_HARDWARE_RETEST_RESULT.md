# RS-001 React Rescue Hardware Retest — Ergebnis

**Datum:** 2026-06-09  
**HEAD:** `27b0829`  
**Version:** `1.7.10.0`  
**RS-001 Status:** **yellow**  
**Lauf-Status:** **teilweise abgeschlossen / Hardware-Retest ausstehend**

---

## Phase 0 — Payload-Gate (bestanden)

| Prüfung | Wert |
|---------|------|
| `payload_update_status` | **success** |
| `verify_status` | **success** |
| `stick_squashfs_hash_ok` | **true** |
| `staging_artifacts_cleaned` | **true** (kein `.sqtmp` auf Stick) |
| `ready_for_operator_retest` | **true** |
| `expected_squashfs_sha256` | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |
| Read-only Verify (Agent) | **success** (`verify-fat32-esp-rescue-usb.sh`) |

Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_latest.json`

---

## Phase 1 — Operator-Hardwaretest

| Feld | Wert |
|------|------|
| Durchgeführt in diesem Lauf | **nein** |
| Grund | Agent hat keinen Zugriff auf UEFI-Cold-Boot der MSI/Referenzhardware |
| Stick eingesteckt am Dev-Host | ja (`/dev/sdb`, nicht gebootet) |

**Operator muss Phase 1 physisch ausführen** (siehe `RS_001_LIVE_MEDIUM_RETEST_HANDOFF.md`).

---

## Phase 2 — Zielzustand (noch nicht bewiesen)

| Kriterium | Beobachtet |
|-----------|------------|
| UEFI USB visible | **unbekannt** |
| GRUB visible | **unbekannt** |
| Kernel starts | **unbekannt** |
| Live system starts | **unbekannt** |
| Old whiptail/OK dialog | **unbekannt** |
| Live-Medium warning | **unbekannt** |
| Network/WLAN blocker before menu | **unbekannt** |
| Telemetry blocker before menu | **unbekannt** |
| React Rescue Shell visible | **unbekannt** |
| Setuphelfer logo/branding visible | **unbekannt** |
| Main menu visible | **unbekannt** |
| Repair/install/backup/restore started | **nein** (kein Boot) |

**Hinweis:** Erwartetes React-Hauptmenü entspricht `RescueStartCenter` (7 Einträge: System analysieren, Backup prüfen, …) — **nicht** dem alten whiptail-Menü.

---

## Phase 3 — Klassifikation

```text
RS-001: yellow
Reason: hardware_retest_not_observed_in_this_run
Prior operator finding (pre-React payload): whiptail dialog, Live-Medium warning — superseded by new squashfs, retest required
```

**Nicht grün** — kein belegbarer React-Shell-Sichtbefund auf Hardware.

---

## Phase 4 — Log-Sammlung (bei fehlender React Shell)

Falls Operator bootet und React Shell **nicht** erscheint, im Live-System ausführen (Befehle aus Strict-Mode Phase 4) und `rs001-react-shell-bootlogs.tgz` nach `SETUPHELFER/setuphelfer/evidence/boot/` kopieren.

Aktuell auf Stick: **keine** `rs001-react-shell-bootlogs.tgz` gefunden.

---

## Bekannte Risiken (vor Retest)

- SquashFS enthält **keinen** vollwertigen Browser (chromium/firefox/links) — React-Rendering auf tty1 kann fehlschlagen
- Start-Assistant delegiert an `setuphelfer-rescue-ui-launch` wenn `rescue.html` vorhanden
- UI zeigt mindestens Text auf tty1 + `http://127.0.0.1:8765/rescue.html`

---

## Next

1. Operator: UEFI-Cold-Boot + Checkliste Phase 1
2. Ergebnis in diese Datei + `RS_001_PHYSICAL_BOOT_RESULT.md` eintragen
3. RS-001 nur **green**, wenn React-Hauptmenü ohne whiptail/Live-Medium-Warnung sichtbar
