# PI-RS-ASUS-PHYSICAL-DIAG-003 – Abschlussbericht

## 1. Workspace und Git

- Hauptworkspace: `/home/volker/piinstaller` (fremde Drift unberührt)
- sauberer Worktree: `/tmp/piinstaller-asus-physical-diag-003`
- Repository: `piinstaller`
- Basiscommit: `d42bcc15` (`origin/pi-rs-asus-diag-bind-002`)
- Feature-Branch: `pi-rs-asus-physical-diag-003`
- HEAD: `bb849af1` (Bericht-Update; Branch-Tip nach Push)
- origin/main: `b8651d33` (Stand Phase 0)
- Push: `origin/pi-rs-asus-physical-diag-003`
- fremde Drift berührt: nein

## 2. Runtime und Payload

- App-Version: `1.9.21.2`
- Runtime-Commit: n/a (kein `/opt`-Runtime-Test in diesem Auftrag)
- Runtime-Gate: ausgesetzt (reine Capture-/Stick-Vorbereitung; kein Live-Backup/Restore)
- Payload-Version: `1.10.2.0`
- Payload geändert: ja (Capture-Modul + TUI/GRUB/i18n inject)
- Payload-SHA256: `5c1ebd83d756250bf60cbc237bf1f9091d099fb96571ed784e43e53f1e96190f`
- USB: Ultra Line `/dev/sda` SETUPHELFER+SETUP_LOGS aktualisiert

## 3. Physischer Lauf

- Run-ID: *ausstehend*
- Boot-ID: *ausstehend*
- Run-Type: `hardware_discovery` (vorbereitet)
- Profil: `asus_rog_gabriel`
- Hersteller/Modell/Board: ASUS / ROG Strix G513QM / G513QM (Soll)
- BIOS: G513QM.331 (Flash verboten)
- Binding: Operator-Phrase im TUI erforderlich
- Write Operations: disabled

## 4./5. NVMe A/B

Noch nicht aus neuem Gabriel-Lauf. Vorwissen (Boot 20260722): PCI `0000:04:00.0` / `0000:05:00.0`, Samsung SM981/PM981-Familie, nvme0 mit p1–p3, nvme1 ohne Partitionen in dmesg. Serienhash/EUI/NGUID/SMART: fehlend → Capture nötig.

## 6. Windows-Partitionen und Boot

Vorwissen unvollständig; efibootmgr ggf. nicht im Image — soft-fail dokumentiert. Vollinventar nach Gabriel-Lauf.

## 7. Windows-Setup-Evidence

- Panther/Rollback: nicht gescannt (Lauf ausstehend)
- Evidence-Qualität: insufficient

## 8. Ursachenbewertung

- wahrscheinlichste Ursache: `unknown`
- Confidence: `low`
- BIOS 335: `plausible` Maßnahme, kein bewiesener Root Cause
- fehlende Evidence: SMART, Error-Log, Panther/Rollback, stabile Serienhashes

## 9. BIOS

- installiert: G513QM.331
- offiziell verfügbar: G513QM.335
- Status: `update_available`
- Flash durchgeführt: nein

## 10. Vorläufige Zielrollen

- noch nicht operator-bestätigt; Schema `role_binding` mit `write_allowed=false` vorbereitet

## 11. Import

- awaiting_physical_run; MSI-Fallback deaktiviert (Bind-002)

## 12. DCC

- `build_gabriel_physical_diag_dcc` ergänzt; Gesamt GELB bis Gabriel-Lauf

## 13. Tests

- neue Unit-Tests PHYSICAL-DIAG-003: bestanden (55 inkl. verwandter ASUS-Tests in Lauf)
- i18n-Parität 4 Locales: ok

## 14. Dokumentation

- Evidence, Operator-Handoff, FAQ DE/EN/FR/NL, Architektur-Notizen, Changelog/Release Notes/Statusmatrix

## 15. Endstatus

`diagnosis_incomplete`

## 16. Nächster Auftrag

- konkrete Maßnahme: Stick auf Gabriels G513QM booten → GRUB Hardwarediagnose → TUI bestätigen → Stick zurück → Import
- BIOS-Update erforderlich: nein (nur optional nach Changelog)
- Windows-Installationsfreigabe: nein
- Linux weiterhin gesperrt: ja

## Import-Nachtrag (Stick zurück, keine TUI)

- Importstatus: `imported_partial_no_new_hardware_discovery`
- Boot-ID: `503549ad-1af5-46fd-bcbb-131aaf5e7b47`
- Kein Post-Inject-Boot; GRUB-Default auf Hardwarediagnose gesetzt
- Endstatus unverändert: `diagnosis_incomplete`
