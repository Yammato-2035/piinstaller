# PI-RS-ASUS-CAPTURE-FINALIZE-004 – Abschlussbericht

## 1. Workspace und Git

- Hauptworkspace: `/home/volker/piinstaller` (fremde Drift unberührt)
- sauberer Worktree: `/tmp/piinstaller-asus-capture-finalize-004`
- Repository: `piinstaller`
- Basis: `b2a19c9f` (vor Serial-Kontamination) + ASUS-Diagnosepfad neu aufgebaut
- Feature-Branch: `pi-rs-asus-capture-finalize-004`
- HEAD: `1f37346f`
- Push: `origin/pi-rs-asus-capture-finalize-004`
- fremde Drift berührt: nein

## 2. Sensitive-Identifier-Audit

- Roh-Identifier im Worktree: nein (Gabriel-NVMe)
- Roh-Identifier in lokaler Clean-Historie: nein
- Roh-Identifier in Remote-Historie: ja — quarantined Feature-Branches
- betroffene Commits (alt): u. a. `b421022a`, `d23cd641` und Vorgänger auf quarantined Tips
- betroffene Branches: `origin/pi-rs-asus-physical-diag-003`, `origin/pi-rs-asus-diag-bind-002`, `origin/pi-rs-asus-win11-linux-001` → **sensitive_history_quarantined**
- Remediation: Fall B — neue saubere Branch-Historie; kein Force-Push auf alte Remotes
- Push-Gate: PASS (`scripts/check-sensitive-hardware-identifiers.sh`)
- vollständige Seriennummer im Bericht: nein

## 3. Baseline-Lauf

- Boot: `c8c60116-…`
- Run: `hw-discovery-20260722T210925Z-0ec17061`
- Status: `running` (nicht terminal)
- letzter Capture-Schritt: NVMe-Identität
- Finalizer erreicht: nein
- SMART: fehlend
- Panther: nicht gestartet
- Completion-Marker: fehlend

## 4. Finalizer-Root-Cause

- primäre Ursache: Capture ohne `finally` vor SMART/Panther abgebrochen; Status blieb `running`
- sekundäre Ursache: Status/Marker erst am Ende; TUI ohne Phasenfortschritt
- betroffene Datei: `backend/core/rescue_hardware_discovery_capture.py`
- Fehlerbehandlung: jetzt try/`finally` + `finalize_capture_artifacts`
- terminaler Status: erzwungen (`complete|partial|failed|cancelled`)
- Confidence: high

## 5. Implementierter Fix

- Capture-Lifecycle: Phasen + Progress-JSON + try/finally
- SMART: Identity-Hash-Re-Resolve + Pflichtfelder
- Panther: RO-Mount; `not_found` ≠ `failed`
- Finalizer: immer; terminal=true
- Manifest / SHA256 vor Completion-Marker
- Completion-Marker: `COMPLETED.TAG` / `PARTIAL.TAG` / `FAILED.TAG`
- TUI: Phasen-Polling, Stick-Hinweise
- GUI-Policy verändert: nein (weiter N/A)
- Storage-Safety verändert: nein (Writes gesperrt)

## 6. Payload und Stick

- App-Version: `1.9.21.2` (unverändert)
- Payload-Version: `1.10.2.1`
- Payload geändert: ja
- SHA256 (squashfs): `7817a515cb93d747029d48edcd399aa62163931349de70d029fb62d365d26357`
- USB: Ultra Line `/dev/sda` (SETUPHELFER + SETUP_LOGS), GRUB default=Hardwarediagnose, `nomodeset`
- Deploy `/opt`: nicht erforderlich für Stick-Rescue-Pfad in diesem Auftrag
- Runtime-Gate: n/a (kein produktiver `/opt`-Lauf)

## 7. Physischer Lauf

- Boot-ID / Run-ID: **ausstehend (Operator-Retest)**
- Profil / Run-Type / Textmodus: vorgesehen `asus_rog_gabriel` / `hardware_discovery` / text
- GUI: `not_applicable_for_text_hardware_discovery`
- NVMe SMART / Error Logs / Panther / Finalizer: nach Retest
- Auto-Shutdown: aus für Discovery-Eintrag

## 8. Import

- Noch kein neuer terminaler ASUS-Run — Import wartet auf Retest
- Filter bereit: Fingerprint + Boot/Run + terminal + Marker; MSI ausgeschlossen

## 9. Windows-Ursachenbewertung

- unverändert unvollständig bis SMART/Panther-Retest
- BIOS 331 / verfügbar 335; Flash nicht autorisiert

## 10. DCC

- Capture: unvollständig bis Retest (gelb)
- GUI-Status: `not_applicable_for_text_hardware_discovery` (nicht rot)
- nächster Schritt: physischer Gabriel-Lauf mit Payload 1.10.2.1

## 11. Tests

- Finalizer / SMART / Panther / Import / TUI-Phasen / GUI-Policy / Safety: pytest PASS
- Sensitive-Identifier-Gate: PASS
- i18n: DE/EN/FR/NL Keys ergänzt
- Gesamt: Unit-Gates grün; physischer End-to-End ausstehend

## 12. Dokumentation

- Capture-Finalizer-Contract, Sensitive-Policy, Runbook, FAQ×4, KB×4, Operator-Handoff: ja

## 13. Endstatus

Endstatus: **diagnosis_incomplete**

(Begründung: Code/Stick/Historie fertig; terminaler physischer Capture auf Gabriel noch nicht ausgeführt.)

## 14. Nächster Auftrag

- Windows-Installationsplanung: nein
- kontrollierter Windows-Retest: nach erfolgreichem terminalem Capture
- BIOS-Update: nicht autorisiert
- Linux weiterhin gesperrt: ja
- verbleibend: Gabriel booten → Capture bis Marker → Stick zurück → Identity-Import
