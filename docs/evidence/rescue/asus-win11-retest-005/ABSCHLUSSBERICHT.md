# PI-RS-ASUS-WIN11-RETEST-005 – Abschlussbericht

## 1. Workspace und Git

- Hauptworkspace: `/home/volker/piinstaller` (nur gelesen; fremde Drift unangetastet)
- sauberer Worktree: `/tmp/piinstaller-asus-win11-retest-005`
- Repository: `Yammato-2035/piinstaller`
- Basis: `origin/pi-rs-asus-capture-finalize-004` @ `da4aec72`
- Feature-Branch: `pi-rs-asus-win11-retest-005`
- HEAD: `9589c21c`
- Push: vorgesehen nach Feature-Commit
- fremde Drift: Hauptworkspace bleibt dirty auf anderem Branch

## 2. Maschine und NVMe

- Gerät: ASUS ROG Strix G513QM (`asus_rog_gabriel`)
- Fingerprint: `79396619c22d7b85…` (hash)
- BIOS: G513QM.331 (2023-02-24); offiziell verfügbar G513QM.335; kein Flash in diesem Auftrag
- Windows-NVMe (provisorisch, unconfirmed): identity `6b45cc50d930…`, EUI `0025385a11b16304`, PCI `0000:00:02.4`, serial_masked `…125Y`
- Linux-NVMe (provisorisch, unconfirmed): identity `ed84d453078b…`, EUI `0025385811911d10`, PCI `0000:00:02.3`, serial_masked `…241F`
- Linux-NVMe-Isolierung: **pending_operator** (physisch bevorzugt)
- SMART: critical_warning=0, media_errors=0, health WARNING (hohe Unsafe-Shutdowns)
- Write-Rechte: alle `false`

## 3. Windows-Medium

- Quelle: offizielles Windows 11 x64 — **Operator** (nicht im Repo)
- Version / Architektur / SHA256 / EFI / boot.wim / install.wim|esd: pending
- Status: `pending_operator_media`

## 4. BIOS-331-Baseline

- Version: G513QM.331
- UEFI: erwartet/true (Operator-Verify vor Stage A)
- Secure Boot / TPM / Bootreihenfolge / Storage: pending Operator-Capture vor Install
- Linux-NVMe isoliert: noch nicht

## 5. Windows-Retest unter BIOS 331

- Run-ID / Start / Ziel / Partitionen / Setup-Phase / Fehler / HRESULT / Win32 / Rollback / Panther / SetupDiag: **nicht gelaufen**
- Ergebnis: pending physical Stage A

## 6. Ursachenbewertung nach Stufe A

- BIOS / NVMe / Medium / GPT/EFI / Treiber / RAM: nicht bewertbar ohne Stage-A-Logs
- wahrscheinlichste Ursache: unbekannt
- Confidence: n/a
- nächste Variable: Operator Stage A unter BIOS 331

## 7. BIOS-335-Update

- durchgeführt: **nein** (Stufe B Gate nicht erreicht)
- Auto-Flash: false

## 8. Windows-Retest unter BIOS 335

- nicht gelaufen

## 9. BIOS-Kausalität

- 331-Ergebnis: not_run
- 335-Ergebnis: not_run
- Bewertung: `not_tested`
- sole_cause_claimed: false

## 10. Windows-Postcheck

- nicht gelaufen; Linux-Gate: **blocked**

## 11. DCC

- BIOS: 331 installiert, Update not_run, Kausalität not_tested
- Windows: Medium pending, Ziel provisorisch, Isolation pending, Install pending
- Fehlerphase: UNKNOWN
- Postcheck: pending
- Linux-Gate: blocked / locked

## 12. i18n und Dokumentation

- de-DE / en-US / fr-FR / nl-NL: Stick-Locales + Frontend-Keys gesetzt
- FAQ: `docs/faq/PI_RS_ASUS_WIN11_RETEST_005_FAQ_{de,en,fr,nl}.md`
- Wissensdatenbank: `docs/knowledge-base/windows-install/WIN11_SETUP_PHASES*`
- Operator-Doku: G513QM Stage A/B, EZ Flash, WinPE Collector, Postcheck
- Architektur: Controlled Retest, WinPE Collection, NVMe Isolation, BIOS Causality, Install Order
- Changelog / Release Notes / Statusmatrix: aktualisiert

## 13. Endstatus

Endstatus: **ready_for_windows_retest_bios331**

## 14. Nächster Auftrag

- BIOS: unverändert 331 für Stage A
- Windows: Operator-Rollenbindung bestätigen → Linux-NVMe isolieren → offizielles Medium prüfen → Stage A + Collector
- Linux: weiterhin gesperrt
- verbleibende Blocker: Operator-Bestätigung Rollen, Isolation, Medium, physischer Installationslauf
- benötigter Operatorlauf: Stage A unter BIOS 331 mit Logerfassung

## Zusatz — Gates

- Runtime-Deploy-Gate: **nicht grün** (`project_version_mismatch` 1.9.21.0≠1.9.21.2 unter `/opt`) → kein `/opt`-Deploy in diesem Lauf
- Sensitive-Identifier-Gate: PASS
- Payload: **1.10.2.3** (Collector-Erweiterung); Stick-Inject ausstehend nach Payload-Build
- App-Version: unverändert **1.9.21.2**
