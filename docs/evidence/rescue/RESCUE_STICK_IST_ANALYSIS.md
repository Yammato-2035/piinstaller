# Setuphelfer Rettungsstick — IST-Analyse

**Analyse-Datum:** 2026-06-08  
**Git HEAD:** `669adb7`  
**Branch:** `main`  
**Projektversion (canonical):** `1.7.9.0` (`config/version.json`)  
**Gate:** `./scripts/check-runtime-deploy-gate.sh` → Exit **20** (`LEGACY_GATE_NON_PROFILE_AWARE`, `/api/dev-dashboard/status` HTTP 404 im Release-Profil; Profil-Gate: `check-runtime-profile-deploy-gate.sh`)  
**Analyse-Modus:** read-only, keine Runtime-Aktionen

---

## 1. Executive Summary

Der Setuphelfer Rettungsstick ist im Repository **architektonisch weit fortgeschritten**, aber **produktiv noch nicht abgenommen**. Der aktive Entwicklungsstrang ist **amd64-first** (Debian Live via `live-build`), mit nachgewiesenem **ISO-Build** (Exit 0, SHA256, UEFI-Post-Patch), **QEMU-Boot-Smoke** (Serial + visuell) und einem **TUI Start Assistant** inkl. Netzwerk-/Telemetrie-Onboarding.

**Rot/offen** bleiben: **Hardware-E2E** (RS-001…RS-008 alle rot; MSI-Laptop bootet trotz validiertem USB-Readback nicht), **Backup/Restore/Verify-Kette auf Rettungsstick** (BR-001-OFFLINE rot), **Provisioning** (kein OS-Rollout vom Stick), **ARM/Pi-Rescue-Images** (deferred), **grafischer Rescue-Wizard**, **Mehrsprachigkeit auf dem Stick** (nur DE), **Secure Boot** (review_required).

Für v1 ist realistisch: **x86_64 UEFI + BIOS (QEMU-nachgewiesen)**, **read-only Diagnose**, **geführtes Netzwerk**, **Telemetrie-Spool**, **Backup-Fund/Verify-Preview**, **Partitions-Preview**. Nicht v1: Pi-Rescue-Stick, Mint/Ubuntu-Installation, vollständiger Restore-Execute, ddrescue, Captive-Portal, globale i18n.

---

## 2. Belegter IST-Stand

| Bereich | IST-Kurz | Primäre Belege |
|---------|----------|----------------|
| Live-Build-Tree | Vorhanden, Bookworm, iso-hybrid | `build/rescue/live-build/setuphelfer-rescue-live/` |
| ISO-Build | Erfolgreich 2026-06-07, 652 MiB, UEFI gepatcht | `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json` |
| UEFI x64 | Deep-Validator grün nach Post-Patch | `scripts/rescue-live/patch-rescue-iso-uefi-x64.sh`, `backend/core/rescue_iso_uefi_classify.py` |
| FAT32-ESP-USB-Alternative | Writer + Verify (Dry-run default) | `backend/core/rescue_fat32_esp_usb_writer.py`, `backend/core/rescue_fat32_esp_usb_verify.py` |
| QEMU Boot | Serial-Smoke grün, visueller Login grün | `docs/evidence/rescue/QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| Start Assistant (TUI) | whiptail-Wizard, wizard-state.json | `scripts/rescue-live/image/setuphelfer-rescue-start-assistant` |
| Netzwerk-Onboarding | NM, WLAN, rfkill, Spool/Retry | `scripts/rescue-live/image/setuphelfer-rescue-network-onboarding`, `setuphelfer-rescue-common.sh` |
| Telemetrie-Ingest | API, LAN-Proxy, Gates | `backend/core/rescue_telemetry_ingest.py`, `backend/core/rescue_network_telemetry_gate.py` |
| Backup/Restore-Engines | Code vorhanden, APIs aktiv | `backend/modules/backup_engine.py`, `restore_engine.py`, `backup_verify.py` |
| Partitionshelfer | Read-only finalisiert | `docs/evidence/partitions/PARTITIONS_FINALIZATION_IST_ANALYSIS.md` |
| Rescue-Testmatrix RS | Alle 8 Einträge **rot** | `docs/testing/RESCUE_STICK_TEST_MATRIX.md` |
| BR-Release-Gate | **rot**, BR-001-OFFLINE blockiert | `docs/evidence/release-gates/backup_restore_release_gate.json` |

### Uncommitted Changes (fremde/parallele Arbeit)

Zum Analysezeitpunkt u. a. geändert: `backend/tests/test_rescue_iso_build_dashboard_state_v1.py`, Rescue-Live-Build-Tree, `ckb-next` (Submodul), diverse `docs/evidence/*`, neue `.cursor/rules/*`, `backend/core/rescue_iso_build_logs.py` (untracked). Diese Analyse berührt keine fremden Änderungen.

---

## 3. Nicht belegbare Annahmen

| Annahme | Status |
|---------|--------|
| MSI-Laptop bootet mit aktueller ISO 1.7.9.0 | **Unbekannt** — letzter Triage: Readback OK, Boot **false** (`RESCUE_USB_UEFI_BOOT_FAILURE_AFTER_VALIDATED_READBACK_TRIAGE.md`) |
| Start Assistant auf physischem Stick = QEMU-Verhalten | **Unbelegt** — nur QEMU/Operator-Evidence |
| Vollständige Backup-Kette auf Stick-HW | **Unbelegt** — BR-001-OFFLINE rot |
| WPA3-Unterstützung explizit getestet | **Unbelegt** — NM/wpawpasupplicant vorhanden, kein WPA3-Test |
| Captive-Portal-Erkennung | **Geplant** (`optional_later` in `runner_rescue_stick_readonly_build_emulation.py`) |
| Französisch/Swahili | **Nicht gefunden** (Grep leer) |

---

## 4. Boot-/Architektur-Stand

| Boot-Modus | Status | Beleg |
|------------|--------|-------|
| x86_64 UEFI | **teilweise** — ISO-Validator grün, HW-Boot offen | `controlled_iso_build_latest_summary.json`, USB-Triage |
| x86_64 Legacy BIOS | **teilweise** — ISOLINUX in ISO, QEMU-Serial grün | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| IA32 UEFI | **geplant** — `review_required` | `docs/knowledge-base/recovery/RESCUE_TARGET_ARCHITECTURES.md` |
| ARM64 UEFI | **geplant/deferred** | `rescue_target_architecture_matrix_latest.json` |
| Raspberry Pi 3B+/4/5 | **nicht gefunden** (als Rescue-Bootmedium) | Architektur-Matrix, `runner_rescue_live_hardware_matrix.py` |
| Secure Boot | **geplant/review_required** | `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md` |
| GRUB-Struktur | **vorhanden** — `BOOTX64.EFI`, `efi.img`, Post-Patch | Build-Log in `controlled_iso_build_latest_summary.json` |
| ISOLINUX | **vorhanden** | `build/rescue/live-build/.../auto/config` |
| squashfs/initrd/vmlinuz | **vorhanden** (Live-Debian-Standard) | Validator `validate-controlled-live-build-tree.sh` |
| Live-System-Build | **vorhanden** | `binary.hybrid.iso` im Build-Tree |
| QEMU-Smoke | **vorhanden** (Serial grün, VM-Smoke teils gelb) | `docs/evidence/runtime-results/rescue/qemu/` |
| Hardware-Boot | **teilweise/offen** | USB-Triage, RS-Matrix rot |

**Multi-Arch-Trennung:** Host `x86_64` → Build-Target `amd64`. Keine Verzeichnisstruktur `/live/arm64/` o. ä. ARM/Pi = separater deferred Track, nicht im x86-ISO-Pfad.

---

## 5. Raspberry-Pi-Stand (inkl. Pi 3B+)

| Aspekt | Status |
|--------|--------|
| Rescue-Stick-Image für Pi | **nicht gefunden** |
| arm64/armhf Build-Track | **deferred** |
| Pi 3B+ USB-Boot-Fallback / microSD-Shim | **nicht gefunden** |
| Pi 4/5 Rescue-Boot | **nicht gefunden** |
| Pi-Config im Squashfs (Hauptprodukt-UI) | **Indiz** — Module im Runtime-Bundle, kein Pi-Boot |
| Setuphelfer auf laufendem Pi installieren | **vorhanden** (Hauptprodukt, `.deb`, `InstallationWizard`) |

**Risiko Pi 3B+:** USB-Boot nicht blind voraussetzen — im Repo **kein** dokumentiertes microSD-Bootshim-/Fallback-Konzept für Rescue.

---

## 6. Backup-/Restore-/Verify-Stand

### Vorhanden (Code)

- Datei-Level: tar.gz + Manifest + SHA256 (`backup_engine.py`)
- Block-Level: `dd` + `sfdisk -d` (allowlisted)
- Verify: basic + deep, gzip-Test, Manifest-Integrität (`backup_verify.py`)
- pigz: optional (`backup_archive_options.py`)
- Restore: preview (default) + execute mit Gates (`restore_engine.py`, `rescue_restore_gate.py`)
- Rescue-Discovery: `rescue_backup_discovery.py`, Deploy-Runner
- Post-Restore-Validation: `post_restore_validation.py` (read-only)
- Dashboard: `BackupRestore.tsx`

### Fehlend / partial

| Funktion | Status |
|----------|--------|
| ddrescue | **nicht gefunden** |
| rsync in Backup/Restore-Pipeline | **nicht gefunden** (nur Clone/Deploy-Hilfsskripte) |
| HW-E2E Full-Root auf Stick | **rot** (BR-001-OFFLINE) |
| Restore-Execute auf Ziel-HW | **partial** — Code + Gates, kein HW-Nachweis |
| Verify nach Restore (HW) | **nicht belegt** (BR-010 Template) |

### Kette Erkennen → Backup → Verify → Restore → Verify

**Nicht evidenced** als durchgängige HW-Kette. Einziger belastbarer Teilketten-Nachweis: **Data-Backup + Verify Deep** auf externem Ziel (nicht Full-Root → Restore → Boot). Release-Gate explizit rot.

---

## 7. Partitionsmanager-Stand

**Read-only finalisiert** (`PARTITIONS_FINALIZATION_IST_ANALYSIS.md`):

- Scan (`lsblk`), Safety-Warnungen, Hardstop-Preview
- Manifest-Layout-Preview (inline + Dateipfad, Allowlist)
- Restore-Handoff-Preview (Verify/BBW/Hardstop)
- UI: `PartitionManager.tsx`, Safety-Panel, Wizard (erklärend, keine Writes)
- API: `/api/partitions/*` — `queue/apply` = Stub, `write_allowed=false`

**Nicht vorhanden (bewusst blockiert):** Partition anlegen/löschen/formatieren/resize, mkfs/fsck-Apply, Dual-Boot-Write, echte Queue-Ausführung.

**Standardfälle heute:** Nur **Vorschau + Gate-Hinweise** — kein geführtes Anwenden.

---

## 8. Provisioning-/Installationsstand

| Ziel | Status |
|------|--------|
| Debian Live (Rescue-Basis) | **vorhanden** (Build-Strang) |
| Debian/Ubuntu/Mint Neuinstallation vom Stick | **nicht gefunden** — explizit blocked in `RESCUE_STICK_PARTITION_HANDOFF.md` |
| cloud-init / autoinstall / preseed (OS-Rollout) | **nicht gefunden** |
| ISO-Download/Cache/SHA256 für Distros | **nicht gefunden** (Provisioning-Layer `missing`) |
| Raspberry Pi OS (32/64/Desktop) vom Rescue-Stick | **nicht gefunden** |
| Rescue plan-builder | **partial** — read-only Pläne, `write_actions_allowed: false` |
| Setuphelfer auf Pi (Hauptprodukt) | **vorhanden** |

Architektur trennt Rescue-MVP, Installer und Provisioning klar (`SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md`).

---

## 9. Netzwerk-/WLAN-/Tethering-Stand

### Vorhanden (Workspace-Code + ISO-Paketliste)

- NetworkManager, wpasupplicant, rfkill, iw, Firmware-Pakete
- Ethernet DHCP/static, Link-Status, Default-Route
- WLAN-Scan, SSID-Auswahl, Hidden-SSID (`setuphelfer-rescue-common.sh`)
- Passwort via whiptail, Secret-Logging-Test
- Offline-Modus + Telemetrie-Spool + Retry-Timer
- Telemetrie-Health-Probe, Dev-Server/LAN-Proxy-Anbindung
- Fehlercodes in `rescue_network_telemetry_gate.py`
- Boot-Menü „Netzwerk-Assistent“ + Onboarding-Service

### Partial / fehlend

| Punkt | Status |
|-------|--------|
| MSI/HW-Retest Netzwerk+Telemetrie | **partial** — Code da, Operator-ISO/USB ausstehend |
| Captive-Portal | **geplant** (`optional_later`) |
| USB-Tethering-Erkennung | **unklar** — kein dediziertes Modul gefunden |
| Download-Geschwindigkeitstest | **nicht gefunden** |
| Mirror-Auswahl/Fallback | **nicht gefunden** (nur APT-Mirror im Build) |
| WPA3 explizit | **unklar** |
| Grafisches Netzwerk-Menü | **nicht gefunden** — TUI/Bash/whiptail only |

---

## 10. Mehrsprachigkeit/i18n-Stand

| Ebene | DE | EN | Weitere |
|-------|----|----|---------|
| Frontend (Desktop/Web) | **vorhanden** | **vorhanden** | — |
| Rescue-TUI (Start Assistant, Netzwerk) | **hardcoded** | **fehlt** | FR/Swahili **nicht gefunden** |
| Rescue-ISO Locale | `de_DE.UTF-8`, Keyboard `de` | — | Validator erzwingt DE |
| Diagnose-API | bilingual (`title_de`/`title_en`) | | |
| Sprachwahl beim Stick-Start | **nicht gefunden** | | |
| Zeitzone ISO | `Europe/Berlin` | | |
| WLAN-Regulatory-Domain | **unklar** | | |

**Außerhalb Deutschlands:** Frontend-i18n reicht für Desktop-App; **Rescue-Stick-TUI ist DE-only** — für Uganda/Kampala-Testfall fehlen Locale/Keyboard/Sprachwahl auf dem Stick.

---

## 11. UI-/Wizard-/TUI-Stand

| Komponente | Status |
|------------|--------|
| Rescue Start Assistant (TUI/whiptail) | **vorhanden** |
| wizard-state.json (GUI-ready Schema) | **vorhanden** — keine GUI-Implementierung |
| Grafischer Rescue-Wizard/Kiosk | **nicht gefunden** |
| Expertenmodus (Shell-Hinweis) | **vorhanden** im Start Assistant |
| Safe-Graphics-Modus | **unklar** auf Rescue-Stick |
| Panda-Begleiter | **vorhanden** in Desktop-Frontend, **nicht** im Rescue-TUI |
| Destruktive Warnungen | **vorhanden** — `execution_allowed: false`, Media-Check |
| Desktop FirstRunWizard / InstallationWizard | **vorhanden** (Hauptprodukt) |

**Fazit:** Rettungsstick braucht für v1 den **TUI-Wizard**; eigener grafischer Rescue-Wizard ist **nicht** implementiert (nur Schema).

---

## 12. Telemetrie-/Anonymisierungsstand

### Drei Kanäle (belegt)

1. **rescue_telemetry** — `/api/rescue/telemetry/*`, Boot-Network-Metadaten, ACK
2. **devserver** — `/api/dev-server/*`, Lab/Beta/Public-Klassen
3. **rescue_agent** — `/api/rescue-agent/*`, Pairing, Heartbeat, E2EE-Stubs

### Zonen A–D (Zielstruktur des Auftrags)

| Zone | Soll | IST |
|------|------|-----|
| A — anonyme Produkttelemetrie | Opt-in, Feld-Allowlist | **partial** — `public_safe_summary`, Upload blockiert in `public_rescue` |
| B — pseudonyme Beta-Session | redacted_beta_extract | **partial** — Dev-Server MVP, `beta_opt_in` |
| C — Vertragsdiagnose | befristete Speicherung | **partial** — Support/Inspect-Kontext, keine explizite Zone-C-Taxonomie |
| D — anonymisierte KB-Erkenntnisse | Pipeline | **geplant** — „FAQ/KB/i18n candidate generator“ später |

**Fehlender Architekturblock:** Explizite **Zone-A–D-Taxonomie** als durchgängiges Telemetrie-Modell **nicht benannt/implementiert**; stattdessen Kanaltrennung + Datenschutz-Klassen in `SETUPHELFER_DEVELOPMENT_SERVER_MVP.md`.

### Privacy-Mechanismen vorhanden

- Token-Trennung, verbotene Felder, Redaction-Client, Secret-Logging-Tests, Spool/Retry, `TELEMETRY-PRIVACY-001` Codes

---

## 13. Wissensdatenbank-/Diagnose-Stand

| Mechanismus | Status |
|-------------|--------|
| Markdown-KB (~199 Dateien) | **vorhanden** |
| FAQ (21 Dateien, DE/EN) | **vorhanden** |
| Diagnose-Registry + API | **vorhanden** — `backend/core/diagnostics/registry.py` |
| Fehlercodes (rescue.*, TELEMETRY-*) | **vorhanden** |
| Hardware-Kompatibilitätsmatrix | **partial** — Runner/Handoff, nicht vollständig befüllt |
| Beta-Feedback → KB | **geplant** |
| Technische KB-Suche-Backend | **nicht gefunden** — Verknüpfung über Registry `related_docs` |

---

## 14. Test-/Evidence-Stand

| Testbereich | Evidence | Ampel |
|-------------|----------|-------|
| Boot x86_64 UEFI (ISO-Validator) | grün | ISO-Struktur OK |
| Boot x86_64 UEFI (HW) | rot/offen | USB-Triage |
| Boot x86_64 Legacy | QEMU Serial grün | partial |
| Boot ARM64 / Pi | nicht gefunden | — |
| QEMU Boot | viele Runs unter `docs/evidence/runtime-results/rescue/qemu/` | partial |
| Netzwerk/WLAN | Workspace-Validator grün, MSI-Retest offen | partial |
| Backup/Restore/Verify E2E | BR-Matrix rot | rot |
| RS-001…RS-008 | alle rot | rot |
| Partitions Preview | Unit-Tests + IST-Analyse grün | grün (read-only) |
| Telemetrie lokal | Ingest-Stub-Smoke, LAN-Proxy | partial |
| i18n Rescue | nur DE | rot für international |
| Grafischer Wizard | nicht implementiert | fehlt |

**Testlücken:** HW-Boot, BR-001-OFFLINE, RS-Matrix, Restore-Execute, Pi-Architekturen, Captive-Portal, Tethering, Provisioning, FR/Swahili.

---

## 15. Risiken und Blocker

| ID | Risiko/Blocker | Schwere |
|----|----------------|---------|
| B1 | HW-UEFI-Boot trotz validiertem Readback | **P0** |
| B2 | BR-001-OFFLINE / RS-Matrix komplett rot | **P0** |
| B3 | Gate Exit 20 (Release-Profil vs. DCC) — Deploy-Drift unklar ohne Profil-Gate | **P1** |
| B4 | Kein End-to-End Backup→Restore→Verify auf Stick | **P0** |
| B5 | Rescue-TUI nur DE — internationale Einsätze blockiert | **P1** |
| B6 | USB-Write/ISO-Build weiterhin Operator-Gates (`usb_write_allowed: false`) | **P1** (Sicherheit, aber verzögert Abnahme) |
| B7 | ARM/Pi deferred — keine Multi-Arch-Abdeckung | **P2** (v1.1+) |
| B8 | Secure Boot ungeklärt | **P2** |
| B9 | Fremde uncommitted Changes im Workspace | **P1** (Reproduzierbarkeit) |
| B10 | Kein ddrescue — defekte Medien schwerer recoverbar | **P2** |

### Abhängigkeiten

```
ISO-Rebuild → USB-Write (Operator) → HW-Boot → Netzwerk/Telemetrie → Backup-Discovery → Verify → (später) Restore
     ↑                                                                              ↑
live-build-Tree                                                          BR-001-OFFLINE Gate
```

---

## 16. v1-Muss-Liste (P0/P1)

| P | Muss für v1 |
|---|-------------|
| P0 | x86_64 UEFI+BIOS ISO bootfähig **auf Referenz-HW** (nicht nur QEMU) |
| P0 | RS-001…RS-004 mindestens grün (Boot, Backend, UI/TUI, Laufwerkserkennung) |
| P0 | Start Assistant End-to-End auf physischem Stick |
| P0 | Netzwerk: Ethernet + WLAN + Offline-Spool auf Referenz-HW |
| P0 | Telemetrie-ACK ohne Secrets auf Referenz-HW |
| P0 | Backup-Fund + Verify-Preview read-only |
| P0 | Media-Check + Hardstops vor destruktiven Plänen |
| P1 | BR-001-OFFLINE: Full-Backup auf stillstehendem FS → Verify Deep |
| P1 | USB-Write-Pfad dokumentiert und reproduzierbar (ISO oder FAT32-ESP) |
| P1 | EN-Fallback für Rescue-TUI (mindestens Hauptmenü) |
| P1 | Fehlercode-Katalog für Netzwerk/Boot konsistent im Stick-UI |

---

## 17. v1.1/v2-Liste

| Phase | Inhalt |
|-------|--------|
| v1.1 | Restore-Execute mit Gates; Partitions-Apply für Standardfälle; FAT32-ESP als Default-Writer |
| v1.1 | Captive-Portal-Hinweis; USB-Tethering-Erkennung; Download-Resume |
| v1.1 | Grafischer Rescue-Wizard (wizard-state.json) |
| v1.1 | Beta-Telemetrie Zone B mit Consent-UI |
| v2 | Provisioning Debian/Ubuntu/Mint; ISO-Cache + Checksums |
| v2 | ARM64 + Raspberry Pi Rescue-Images; Pi 3B+ microSD-Fallback |
| v2 | ddrescue; block-level mit defekten Sektoren |
| v2 | Secure Boot (Shim-Signierung) |
| v2 | FR/Swahili + Locale/Keyboard/Zeitzone-Auswahl beim Boot |
| v2 | Zone-D KB-Pipeline aus anonymisierten Telemetrie-Ereignissen |

---

## 18. Empfehlungen für den nächsten Umsetzungs-Prompt

1. **Phase „HW-Boot-Schließen“** zuerst: ISO 1.7.9.0 rebuild → USB-Write (Operator) → MSI/Referenz-Laptop → RS-001/002 dokumentieren; USB-Triage-Fehlermodus vom Operator einfordern.
2. **Phase „Netzwerk+Telemetrie HW“**: LAN-Proxy, Onboarding, ACK, Task-Pull auf gleicher HW; Evidence nach `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT_TEMPLATE.md`.
3. **Phase „Read-only Rescue-Flow“**: Start Assistant → Disk-Discovery → Backup-Fund → Verify-Preview; RS-003…007 grün machen.
4. **Phase „BR-001-OFFLINE“**: nur nach Phase 1–3; Full-Root auf externem Ziel, kein Live-Desktop-Retry.
5. **Nicht parallel starten:** Provisioning, Pi-Images, Partitions-Write, Restore-Execute — harte Gates erst nach BR-001-OFFLINE-Teilnachweis.
6. **Sicherheitsregeln** in jeden Folge-Prompt: Phase-0-Gate, Operator-Confirm für ISO/USB, kein auto-write, Dry-run default, fremde Changes nicht anfassen.
7. **Erste Module:** `scripts/rescue-live/*`, `backend/core/rescue_*`, `rescue_backup_discovery.py`, `rescue_network_telemetry_gate.py` — nicht `partitionshelfer` Write-Pfad.

---

*Erstellt als reine IST-Analyse. Keine Codeänderungen, kein Commit.*
