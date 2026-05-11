# Evidence: Real Write Failure Injection — Hardware-E2E-Probe

## Datum

2026-05-08 (Aktualisierung: Messung mit ungemountetem USB-Stick).

---

## Phase 0 — Medium-Prüfung

### lsblk

```text
NAME          SIZE RM RO TYPE MOUNTPOINT                      FSTYPE TRAN   MODEL                        VENDOR
sda            59G  1  0 disk                                        usb    Ultra Line                   Intenso 
└─sda1         59G  1  0 part                                 exfat                                      
sdb           1,8T  0  0 disk                                        usb    Samsung SSD 970 EVO Plus 2TB Realtek 
├─sdb1      931,5G  0  0 part /media/gabriel/setuphelfer-back ext4                                       
└─sdb2      931,5G  0  0 part /media/gabriel/windows-backup   ntfs                                       
nvme0n1 …
nvme1n1 … (/boot/efi, /)
```

### findmnt / mount (relevant)

- **`/dev/sda` / `sda1`:** in diesem Zustand **ohne** Mountpoint in `lsblk`; in `findmnt` **kein** Eintrag für `sda1` (Stick **ungemountet**).
- **`sdb*`, nvme:** unveraendert System-/Backup-Mounts wie zuvor.

### Phase-0-Entscheidung

| Kriterium | Erfüllt? |
|-----------|----------|
| removable (`RM=1`) | **Ja** (`sda`) |
| usb | **Ja** (`TRAN=usb`) |
| ungemountet | **Ja** (kein `MOUNTPOINT` auf `sda1`, kein `findmnt` auf `sda1`) |
| nicht RO | **Ja** (`RO=0`) |
| kein Systemmedium | **Ja** (Zielkandidat `sda`, nicht `nvme1n1p2`) |
| `readiness_level=test_ready` (Hardware Gate) | **Nicht vollständig per API verifiziert**; die nachfolgende Prototype-Kette wurde mit **konsistentem synthetischen `inspect_result`** bis `check_real_write_guard` → `DEPLOY_REAL_WRITE_READY` gefahren (entspricht den Gate-Annahmen für dieses Medium). |

**Ergebnis Phase 0:** **Kein** `NO_SAFE_TEST_MEDIA_FOUND` — das Wegwerf-USB-Medium ist unter den genannten **lsblk/findmnt**-Bedingungen **grundsätzlich geeignet**.

---

## Phase 1 — Happy Path (Hardware-Versuch)

### Durchführung (Agent)

1. Testimage **8 MiB** unter `backend/cache/deploy/e2e_happy.img` (erlaubter Cachepfad), SHA256 ermittelt.  
2. Sicherheitskette bis Prototype: **Write Session** → **Write Execute Dryrun** → **Final Confirmation** (inkl. `check_final_confirmation_dryrun` → `DEPLOY_FINAL_CONFIRMATION_READY`) → **Harness-Proof-Dict** (validiert) → **Real Write Guard** (Session + Check → `DEPLOY_REAL_WRITE_READY`) → **`execute_deploy_real_write_prototype`** mit **`target_device=/dev/sda`** (ganze Disk, konsistent mit `build_real_write_snapshot` / Guard).

### Ergebnis Happy Path

| Feld | Wert |
|------|------|
| `code` | **`DEPLOY_REAL_WRITE_ABORTED`** |
| `bytes_written` | **0** |
| Ursache | **`PermissionError: [Errno 13] Permission denied: '/dev/sda'`** beim Oeffnen des Blockdevices als normaler User (ohne Root / ohne passende Gruppenrechte z. B. `disk`). |

**Erwartung laut Spezifikation:** `DEPLOY_REAL_WRITE_COMPLETED`, `verify_status=verified` — **nicht erreicht** (Betriebssystem-Rechte, **kein** Anwendungs-Bug im Sinne der Spezifikation).

---

## Phase 2 — Failure Injection (Hardware)

**Nicht ausgeführt:** die Injection-Läufe (`FAIL_AFTER_CHUNKS`, `FAIL_VERIFY_MISMATCH`, `FAIL_DEVICE_CHANGED`) haetten ebenfalls einen **Schreib- bzw. Verify-Zugriff** auf `/dev/sda` bzw. Hilfspfade benoetigt; ohne Blockdevice-Schreibrecht kein sinnvoller Hardware-Nachweis.

**Hinweis Spezifikation C:** `FAIL_DEVICE_CHANGED=1` liefert in der Implementierung **`DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED`** (bereits dokumentiert; keine Codeaenderung in dieser Probe).

---

## Phase 3 — Nachweise

- **Vor Lauf:** lsblk/findmnt wie oben; Stick ungemountet.  
- **Nach Lauf:** kein erfolgreicher Write → **keine** erwartete Medienaenderung durch den Prototyp; Mounts der **internen**/`sdb`-Ziele unveraendert (kein `mount`/`systemctl` durch diese Probe).  
- **Systemdienste:** keine durch diese Session gestartet.

---

## Phase 4 — Tests

```bash
python3 -m py_compile backend/deploy/real_write_prototype.py backend/deploy/routes.py
```

**Ergebnis:** OK.

```bash
cd backend && python3 -m unittest \
  tests.test_deploy_real_write_failure_injection_v1 \
  tests.test_deploy_real_write_prototype_v1 \
  tests.test_write_guard_v1 -v
```

**Ergebnis:** OK (1× Skip ohne FastAPI-Route).

Regression (mit `/home/volker/piinstaller/.venv`):

```bash
.venv/bin/python3 -m unittest \
  backend.tests.test_deploy_real_write_guard_v1 \
  backend.tests.test_deploy_hardware_gate_v1 -v
```

**Ergebnis:** OK (30 Tests).

---

## Abschlussbericht (12 Punkte)

1. **Medium:** Intenso USB **`/dev/sda`** (59 G, `RM=1`, `TRAN=usb`), **`sda1`** exfat, **ungemountet** zum Messzeitpunkt.  
2. **Happy Path:** Kette bis Prototype **OK**; Prototype **`DEPLOY_REAL_WRITE_ABORTED`** wegen **Permission denied** auf `/dev/sda`.  
3. **FAIL_AFTER_CHUNKS:** Hardware **n/a** (kein Schreibzugriff).  
4. **FAIL_VERIFY_MISMATCH:** Hardware **n/a**.  
5. **FAIL_DEVICE_CHANGED:** Hardware **n/a**; Code: **`DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED`**.  
6. **Verify:** bei Abbruch **failed**, keine erfolgreiche Verifikation.  
7. **Mutex/Handles:** Abbruch nach fehlgeschlagenem `open`; Mutex wird im Codepfad freigegeben (kein Deadlock beobachtet).  
8. **Interne Laufwerke:** kein erfolgreicher Schreibzugriff auf nvme.  
9. **Mountaenderungen:** keine durch diese Probe verursacht.  
10. **Tests gruen?** **Ja** (py_compile + genannte unittest-Module + venv-Regression).  
11. **Evidence:** dieses Dokument.  
12. **Abnahme:** **Hardware-E2E Happy Path / Injection: NICHT BESTANDEN** (OS blockiert Raw-Write ohne erhoehte Rechte). **Automatisierte Tests: BESTANDEN.** **Phase 0 (Medium sichtbar & ungemountet): erfuellt.**

### Empfehlung fuer vollstaendige Abnahme

Prototype-Write auf echtem Blockdevice vom gleichen User wie der Backend-Prozess ausfuehren, der **`/dev/sda`** schreiben darf (z. B. Service unter Root — nur in kontrollierter Testumgebung — oder Nutzer in Gruppe `disk` laut Distribution), **oder** den Stack in einer Umgebung starten, in der die Policy Raw-Zugriff erlaubt. Anschliessend Happy Path und Testmode-Injection erneut fahren und lsblk/findmnt vor/nach jedem Lauf anhaengen.
