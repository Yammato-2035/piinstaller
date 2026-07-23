# PLANNING_MATRIX — PI-RS-ASUS-LAB-CONTROL-006

## Kritischer Pfad (gewählt)

**A — instrumentierter Windows-Setup-Lauf mit Live-Capture**

Begründung: größter Kausalitätsgewinn vor Firmware-/Mint-Änderung; Payload-/Collector-Lücke ist belegt; Mount-Tooling ist nicht mehr Blocker.

Verworfen für diesen physischen Hauptlauf (plan-only vorbereitet):

- **B BIOS 335 zuerst** — ohne Setup-Artefakte vermischt Kausalität; Preflight noch nicht ready.
- **C Mint auf linux_lab_nvme zuerst** — ändert EFI/Bootorder vor instrumentiertem Setup.

## Planstatus nach Self-Review: `ready` (für Implementierung + Stick-Prep; physischer Setup-Lauf Operator)

---

## Matrix (Pflichtfelder)

| ID | Ziel | Beobachteter Ist-Stand | Annahmen | Zielmaschine | Zielmedium | Aktion | Risikoklasse | Freigabe | BitLocker | Reversibilität | Preflight | Evidence vorher | Evidence während | Evidence danach | Rollback | Stop | Remote | Operator vor Ort | Test | Erfolg | Folge |
|----|------|------------------------|----------|--------------|------------|--------|--------------|----------|-----------|----------------|-----------|-----------------|------------------|-----------------|----------|------|--------|------------------|------|--------|-------|
| P01 | Last-Boot finalisieren | 095959Z, mount OK, 0 Panther | — | G513QM hash `7939…` | Windows NVMe hash `6b45…` | Analyse + JSON | read_only | erlaubt | none | voll | Identity lesen | Stick-Run | — | LAST_BOOT_* | n/a | — | ja | nein | Unit/Evidence | JSON vollständig | P02 |
| P02 | Lab-Profil YAML | Identity aus Capture | Rollen unconfirmed | ASUS_ROG_GABRIEL_LAB | beide NVMe hashes | `config/lab-targets/asus-rog-gabriel.yaml` | read_only | erlaubt | none | voll | Hashes aus Evidence | machine_identity | — | MACHINE_IDENTITY_* | Profil löschen | mismatch | ja | nein | Unit | exact_match Schema | P03 |
| P03 | Autorisierung machine-bound | Gabriel-Bind existiert | Operator-Phrase | nur G513QM | fingerprints | Auth-Modul + Gates | controlled | erlaubt | none | voll | exact_match | profile | — | AUTHORIZATION_* | disable profile | MSI/Dev | ja | nein | Unit Auth | MSI blocked | P04 |
| P04 | BitLocker hard-block | RO-Policy vorhanden | Keys nie speichern | Lab | n/a | Mutation-Deny-List | controlled | erlaubt | prohibited | voll | Pattern-Tests | — | — | policy JSON | n/a | mutation attempt | ja | nein | Unit | mutation blocked | P05 |
| P05 | Live-Capture WinPE | Collector ohne periodischen Heartbeat; unknown-norunid | Setup schreibt irgendwann Panther | Lab | SETUP_LOGS label | Run-ID + Heartbeat + Flush | controlled | erlaubt | none | voll | SETUP_LOGS write test | TAG | heartbeats | WIN_CAPTURE_* | Collector stop | no SETUP_LOGS | teilweise | **ja** (Setup) | Unit+phys | evidence_collected oder insufficient mit Heartbeats | P06 |
| P06 | Setup-Wrapper | Setup-Flags unklar | `/noreboot` nur wenn belegt | Lab | Stick | Wrapper dokumentiert Aufruf | controlled | erlaubt | none | teil | Flag-Verify | wrapper meta | exitcode | result/ | n/a | unsupported flag | nein | ja | Integration | exitcode logged | P07 |
| P07 | Remote Job Contract | rescue_remote Allowlist | mTLS/Token bestehend | Lab fingerprint | — | Job-Schema erweitern; ASUS-only shell | controlled | erlaubt | prohibited | voll | signature+nonce+expiry | job json | stream | REMOTE_AGENT_* | cancel | wrong profile | ja | nein | Unit | replay blocked | P08 |
| P08 | Payload/Stick | 1.10.2.9 physisch | Build=Stick | Stick Ultra Line | ESP squashfs | Bump 1.10.3.0 + inject | controlled | erlaubt | none | teil | SHA256 gate | manifest | — | payload tag | vorherige squashfs backup | SHA mismatch | nein | ja | Packaging | SHA match | P09 |
| P09 | Instrumentierter Setup | Freeze historisch | Live-Capture fängt Artefakte | Lab | Win NVMe | Operator Setup + Collector | destructive* | bedingt | indirect_possible (TPM/SB später) | nicht | P05–P08 | Pre-state | heartbeats | Import | Image restore plan | no run_id | nein | **ja** | physical | Run-ID gültig | P10 |
| P10 | BIOS 335 Decision | 331 installed | 335 official for G513QM | Lab | Firmware | Decision doc only diesmal | firmware | plan-only | indirect_possible | nicht | exact model+hash+AC | bios inventory | — | BIOS_335_DECISION | EZ Flash reverse N/A | wrong model | teilweise | ja for flash | — | decide after P09 | later |
| P11 | Mint Lab Node | nvme1 GPT empty | role linux_lab_nvme | Lab | Linux hash `ed84…` | Decision + layout plan | destructive | plan-only | none | teil | fingerprint recheck | disk inventory | — | MINT_NODE_DECISION | reinstall | wrong disk | teilweise | ja | — | after evidence | later |

\*Setup selbst ist destruktiv auf Windows-NVMe; Collector ist read-only auf Stick.

## Hypothesen (Kurz)

| Thema | BEOBACHTET | ABGELEITET | UNBEKANNT | WIDERLEGT |
|-------|------------|------------|-----------|-----------|
| Mount-Tooling | ntfs-3g RO OK | GLIBC nicht Ursache | — | „Mount blockiert Logs“ |
| Fehlende Panther | 0 Dateien auf Volume | Post-Hang Scan allein unzureichend | Setup-Phase bis Hang | „definitiv vor Panther abgebrochen“ |
| BIOS 335 | Version 331 | — | Kausalität Freeze | „335 nötig weil Freeze“ ohne Logs |

## BitLocker-Hinweis

Freigegebene Firmware-/Secure-Boot-/TPM-Schritte können **indirekt** Recovery auslösen. Mutation bleibt verboten; vor solchen Schritten nur RO-Status erfassen und Operator warnen.
