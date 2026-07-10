# PI-RS-BUILD-001 — Payload-/Build-Entscheidung für MSI-Retest

Stand: 2026-07-10  
Repo: `/home/volker/piinstaller` @ `e913367` (BUILD-001-Doku-Commit, origin/main)

## Ausgangsstand

| Feld | Wert |
|------|------|
| Projektversion (Workspace) | **1.9.19.4** |
| PI-RS-TEL-003 | Cross-Repo Preview verifiziert (CSE `0.1.0-lab2`, DIAG-LAB-003), `preview_only=true` |
| PI-RS-WT-004 | Working Tree sauber, Full Gate grün (94 Tests) |
| WT-004 Backup persistent | `/home/volker/setuphelfer-backups/pi-rs-wt004-20260710-081359` (180 MB) |

## Full Gate vor Build-Entscheidung

`run-tests.sh`: **grün**

| Block | Ergebnis |
|-------|----------|
| DCC-VIS-001 Frontend (npm/vitest) | 18 passed |
| PI-RS-TEL-001 | 23 passed |
| PI-RS-TEL-002 | 34 passed |
| PI-RS-TEL-003 | 19 passed |
| Safety Gates TEL-001/002 | ok |

Evidence: `docs/evidence/pi_rs_build_001_payload_build_decision_msi_retest/full-run-tests-before-build.txt`

## USB-Inventur (nur Lesen)

| Gerät | Label | Größe | Mount |
|-------|-------|-------|-------|
| `sda1` | SETUPHELFER | 4G vfat | `/media/volker/SETUPHELFER` (ro) |
| `sda2` | SETUP_LOGS | 55G vfat | `/media/volker/SETUP_LOGS` (rw) |

**USB-Schreiboperation:** **nein** (kein Operator-Go in diesem Sprint).

## Vorhandene Payload-Basis (lokal, nicht committed)

| Artefakt | Version | Größe | SHA256 |
|----------|---------|-------|--------|
| `build/rescue/filesystem.squashfs.repacked-1.10.0.12` | 1.10.0.12 | 1,2 GB | `1a72046a40a504e62771a8fc8cd4b6360951c3ac0a4e352a8248fc68f14487e6` |
| `build/rescue/binary.hybrid.repacked-1.10.0.3.iso` | 1.10.0.3 | 1,3 GB | (älter als neuestes SquashFS) |

**Hinweis:** Projektversion **1.9.19.4** und Payload-Track **1.10.0.12** weichen ab. Repack würde `filesystem.squashfs.repacked-1.9.19.4` erzeugen (aus `config/version.json`), Quelle wäre aktuell 1.10.0.12.

## Build-Optionen A–E

| Option | Bewertung | Ergebnis |
|--------|-----------|----------|
| **A) no-build / deferred** | PI-RS-TEL-003 ist Preview-/Lab-Verifikation ohne Produktivsend; MSI-Hardware-Retest kann zunächst mit bestehendem Stick/Payload erfolgen | **gewählt** |
| **B) metadata-only** | Version in Workspace bereits 1.9.19.4; Stick-Payload würde weiterhin alte Runtime tragen | **nicht ausreichend** für MSI-Retest mit 1.9.19.4-Inhalten |
| **C) payload repack** | Script `repack-rescue-squashfs-react-shell.sh` vorhanden, kein `--dry-run`; würde Backend (inkl. TEL-003) syncen; ~1,2 GB, UI-Smoke-Gate, Zeit/Disk | **deferred** → PI-RS-MSI-RETEST-001 |
| **D) full build** | `run-controlled-iso-build-with-logging.sh` / lb — deutlich schwerer, nicht nötig für TEL-003-Preview | **abgelehnt** |
| **E) USB writer/update** | Stick erkannt, aber kein Schreiben ohne separates Operator-Go | **deferred** |

## Entscheidung

**`no-build / deferred`** (mit `payload_repack_deferred`, `usb_update_deferred`)

### Begründung

1. PI-RS-TEL-003 liefert **Cross-Repo Preview Verification** auf dem Entwicklungsrechner (localhost Diagnostics) — kein zwingender neuer Stick-Payload für den Verifikationsnachweis.
2. Vorhandenes SquashFS **1.10.0.12** ist reproduzierbar dokumentiert; ISO **1.10.0.3** hinkt hinterher — vor MSI-Retest ist explizit zu klären, ob Retest mit **1.10.0.12** oder nach **Repack auf 1.9.19.4** erfolgen soll.
3. Repack-Script hat **keinen Dry-Run**; Ausführung wäre ein schwerer, irreversibler Operator-Schritt — gehört in **PI-RS-MSI-RETEST-001** mit klarem Scope.
4. Full Gate ist grün; **kein Build-Blocker** aus Tests.
5. USB-Stick ist angeschlossen, wurde **nicht** beschrieben (Sprint-Grenze).

## MSI-Retest-Readiness

| Kriterium | Status |
|-----------|--------|
| Workspace sauber + Gate grün | ja |
| Version 1.9.19.4 im Repo | ja |
| Payload 1.9.19.4 auf Stick/ISO | **nein** (deferred) |
| Stick physisch verfügbar | ja (SETUPHELFER + SETUP_LOGS) |
| Produktiv-Telemetry/Diagnostics Send | nein (weiterhin preview_only) |

## Risiken

- Payload-/Projekt-Versions-Drift (1.10.0.12 vs 1.9.19.4) kann MSI-Retest-Ergebnisse verfälschen, wenn nicht dokumentiert.
- WT-004 WIP-Backup ist jetzt persistent unter `/home/volker/setuphelfer-backups/`.
- Root-owned `fat32_esp_*` Remnants weiterhin auf Platte (gitignoriert).

## Nächster Schritt

**PI-RS-MSI-RETEST-001** — MSI GE63 Raider Retest:

1. Operator-Entscheid: Retest mit **bestehendem 1.10.0.12-Payload** oder vorher **Repack** (`repack-rescue-squashfs-react-shell.sh`) auf **1.9.19.4**.
2. Optional: `write-fat32-esp-rescue-usb.sh` nur mit explizitem Operator-Go.
3. Alternativ ohne Stick-Build: **PI-RS-LIVE-001** (localhost/lab-only Send-Test).
