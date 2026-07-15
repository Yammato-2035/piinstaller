# MSI Auto-E2E Failure Analysis — Payload 1.10.0.22 Boot 2026-07-15

## Kontext

| Feld | Wert |
|------|------|
| Boot-Datum | 2026-07-15 ~09:39 UTC |
| Payload | **1.10.0.22** |
| Workspace-Stand auf Stick | vor Commit `695e3652` (001D4 unvollständig im SquashFS) |
| MSI | GE63 Raider RGB 8RF |
| SABRENT-HDD | erkannt, nicht genutzt |

## Pflichtbefunde

| Befund | Status | Evidenz |
|--------|--------|---------|
| Payload 1.10.0.22 | **belegt** | `current-session.json`, `lab-auto-result.json` |
| MSI-Evidence bestanden | **belegt** | `lab-auto-result.json`: `result_status=passed`, Uptime 158s |
| Physical E2E nicht ausgeführt/persistiert | **belegt** | Kein `e2e-rescue-msi-*` auf SETUP_LOGS |
| Neuer e2e-rescue-msi-Run fehlt | **belegt** | Nur alter Dev-Lauf `e2e-rescue-physical-20260714-153401-d35375d0` |
| SABRENT-HDD erkannt | **belegt** | `lsblk.json`: `/dev/sdb` SABRENT, Label `Backup` |
| SABRENT-HDD genutzt | **nein — belegt** | Kein Mount, kein Marker, kein Run-State |
| TUI durch Evidence beeinträchtigt | **stark wahrscheinlich** | Late-Evidence zeigt whiptail; Evidence-Service ohne TTY-Lock in Unit 1.10.0.22 |
| Run-Control nicht verbraucht | **belegt** | `run-control.json`: `enabled=true`, `consumed` fehlt |
| Shutdown/E2E-Abschluss nicht belegt | **belegt** | Kein `shutdown-evidence.json`, kein `auto-physical-e2e-result.json` |

## Root Cause (001D5 Adressierung)

### 1. Payload 1.10.0.22 ohne vollständigen 001D4/001D5-Stand

**Belegt.** SquashFS gebaut bei Commit `3c753941` / `bafce68e`, vor `695e3652`. Run-Control auf SETUP_LOGS vorhanden, Orchestrator-Code im Stick-SquashFS unvollständig.

### 2. Evidence-Service und TUI-Konsole

**Stark wahrscheinlich.** `auto-msi-evidence` lief parallel zur TUI ohne explizite TTY-Isolation (`StandardInput=null`, `TTYPath=` fehlten in 1.10.0.22). Lab-Modus übersprang TUI-Wartezeit.

**001D5-Fix:** Journal-only für Hintergrunddienste, TUI Auto-Lock-Modus, `setuphelfer-rescue-tui.service`.

### 3. Physical E2E wartete, persistierte nicht

**Belegt.** `50-systemd-jobs.txt` (09:39:20): `auto-physical-e2e.service start waiting`. Diagnose-Snapshot vor Late-Gate (09:41:43). Kein terminaler Run auf SETUP_LOGS.

**Stark wahrscheinlich:** Wrapper prüfte Exit nur bei `msi_e2e_auto_passed`, nicht 001D4-Statuswerte.

**001D5-Fix:** Gate auf `msi-evidence-complete.json`, Exit über `is_physical_e2e_success_status()`.

### 4. Run-Control nicht verbraucht

**Belegt.** E2E erreichte keinen terminalen Zustand → `consume_run_control()` nicht aufgerufen.

**001D5-Fix:** Consumption bei passed/failed/blocked/cancelled/timeout.

### 5. SABRENT ohne Marker/Mount

**Belegt.** `lsblk.json`: UUID `44ce6f76-7896-4623-87b0-d81aedbed6d5`, `mountpoint: null`. 001D4 verlangte `setuphelfer-e2e-target.json` + Mount.

**001D5-Fix:** `destructive_lab_target` in Run-Control, mehrstufige Identität, keine Markerpflicht, Selbst-Mount.

### 6. Fallback-Shutdown

**Noch zu testen** am MSI. Failsafe-Timer 420s konnte parallelen Lauf stören.

**001D5-Fix:** Failsafe prüft Heartbeat und aktiven E2E-Service.

### 7. Kein TUI Auto-Testmodus

**Belegt** (Code-Stand 1.10.0.22). Normales 10-Punkte-Menü aktiv.

**001D5-Fix:** Modus `auto_physical_e2e_locked`, nur Abbrechen/Herunterfahren.

## Systemd-Zustand beim Diagnose-Snapshot

```text
setuphelfer-rescue-auto-msi-evidence.service  running
setuphelfer-rescue-auto-physical-e2e.service  waiting
```

## SABRENT-HDD (MSI)

```text
/dev/sdb     SABRENT USB  ~931 GB  tran=usb  role=external_backup_hdd
/dev/sdb1    ext4  Label=Backup  UUID=44ce6f76-7896-4623-87b0-d81aedbed6d5  mount=null
```

## Nächster Lauf (001D5)

- Payload **1.10.0.23** mit destruktivem SABRENT-Gate
- Neues Run-Control mit `destructive_lab_target`
- MSI-Boot mit Setuphelfer-Stick + SABRENT-HDD
