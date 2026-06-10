# Setuphelfer Rettungsstick — Gap-Liste

**Analyse-Datum:** 2026-06-10 · **HEAD:** Fix `1.7.11.0` · **Branch:** `main`

Prioritäten: **P0** = zwingend v1 · **P1** = wichtig v1 · **P2** = v1.1 · **P3** = v2/später

| Bereich | Soll-Funktion | IST-Status | Beleg | Risiko | Priorität | Empfohlene Phase |
|---------|---------------|------------|-------|--------|-----------|------------------|
| Boot | RS-001 Stick Acceptance | partial (L1–2 ok, L3–4 review) | `RS_001_STICK_ACCEPTANCE_RESULT.md` | Hardware blockiert | P0 | Rebuild + Acceptance grün |
| Boot | x86_64 UEFI HW-Boot | partial (gelb; Acceptance vor HW) | `RS_001_REACT_RESCUE_HARDWARE_RETEST_RESULT.md` | Netzwerk-Crash; kein GRUB-Theme | P0 | Acceptance ok → HW-Retest |
| Boot | x86_64 Legacy BIOS HW | partial (QEMU only) | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` | Ältere BIOS-Geräte | P1 | Phase 1 |
| Boot | RS-001…RS-008 grün | missing (alle rot) | `docs/testing/RESCUE_STICK_TEST_MATRIX.md` | Kein Release-Nachweis | P0 | Phase 1–3 |
| Boot | ARM64 Rescue-Image | planned/deferred | `RESCUE_TARGET_ARCHITECTURES.md` | Keine ARM-Laptops/Pi | P3 | v2 |
| Boot | Raspberry Pi 3B+ Rescue | missing | Architektur-Matrix | USB-Boot unsicher | P3 | v2 |
| Boot | Pi 3B+ microSD-Fallback | missing | — | Pi3 ohne USB-Boot tot | P3 | v2 |
| Boot | Secure Boot | planned | `SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md` | UEFI-SB-Geräte | P3 | v2 |
| Discovery | Laufwerke auf Stick HW | partial | RS-004 rot | Diagnose blockiert | P0 | Phase 2 |
| Backup | Full-Root auf Stick (BR-001-OFFLINE) | missing (rot) | `backup_restore_release_gate.json` | Kern-Use-Case blockiert | P0 | Phase 4 |
| Backup | ddrescue | missing | Grep leer | Defekte Platten | P2 | v1.1 |
| Backup | rsync in Backup-Pipeline | missing | Nur Clone-Pfad | Alternative fehlt | P3 | v2 |
| Backup | Block-Level dd | partial | `backup_engine.py` | Code da, HW rot | P1 | Phase 4 |
| Verify | Verify Deep auf Stick-HW | partial | BR-004/005 blocked | Restore-Vorbereitung unsicher | P0 | Phase 4 |
| Restore | Echter Restore Execute | partial | `rescue_restore_gate.py` | Nur Preview im MVP | P2 | v1.1 |
| Restore | Verify nach Restore | missing | BR-010 Template | Keine Abschlusskette | P2 | v1.1 |
| Restore | E2E Erkennen→Backup→Verify→Restore→Verify | missing | Release-Gate rot | Produktversprechen unbelegt | P0 | Phase 4 |
| Partition | Geführte Standardfälle anwenden | missing (read-only) | `PARTITIONS_FINALIZATION_IST_ANALYSIS.md` | Nutzer muss GParted | P2 | v1.1 |
| Partition | Resize/mkfs/fsck Apply | missing | `partitionshelfer/README.md` | Bewusst blockiert | P2 | v1.1 |
| Partition | Dual-Boot-Vorbereitung Write | missing | Partition-Handoff | Nur Preview | P3 | v2 |
| Provisioning | Debian Neuinstallation | missing | `RESCUE_STICK_PARTITION_HANDOFF.md` | Nur Rescue, kein Install | P3 | v2 |
| Provisioning | Ubuntu Server LTS | missing | Architektur-Abgrenzung | — | P3 | v2 |
| Provisioning | Linux Mint Cinnamon/Xfce | missing | Partition-Handoff | — | P3 | v2 |
| Provisioning | Raspberry Pi OS (32/64/Desktop) | missing | `SD_CARD_IMAGE.md` | Pi nur Hauptprodukt | P3 | v2 |
| Provisioning | ISO-Cache + SHA256/GPG | missing | component_inventory | Offline-Install | P3 | v2 |
| Netzwerk | Ethernet auf Referenz-HW | partial | Onboarding-Skript | MSI-Retest offen | P0 | Phase 2 |
| Netzwerk | WLAN Scan/Connect HW | partial | `setuphelfer-rescue-common.sh` | MSI-Retest offen | P0 | Phase 2 |
| Netzwerk | Hidden SSID | present | `setuphelfer-rescue-common.sh` | — | P1 | — |
| Netzwerk | WPA3 explizit | unclear | NM-Pakete | Neue Geräte | P2 | v1.1 |
| Netzwerk | Captive Portal | planned | `runner_rescue_stick_readonly_build_emulation.py` | Hotel-WLAN | P2 | v1.1 |
| Netzwerk | USB-Tethering | unclear | — | Mobilfunk-Fallback | P2 | v1.1 |
| Netzwerk | Download-Geschwindigkeitstest | missing | — | Provisioning-Vorbereitung | P3 | v2 |
| Netzwerk | Mirror-Fallback | missing | — | APT/ISO-Downloads | P3 | v2 |
| i18n | Sprachwahl Stick-Start | missing | Start-Assistant DE-only | International | P1 | Phase 3 |
| i18n | Englisch Rescue-TUI | missing | `de.json` nur Frontend | EN-Nutzer | P1 | Phase 3 |
| i18n | Französisch | missing | Grep leer | FR-Region | P3 | v2 |
| i18n | Swahili | missing | Grep leer | Uganda-Testfall | P3 | v2 |
| i18n | Locale/Keyboard/Zeitzone wählbar | partial (fest DE) | `validate-rescue-iso-squashfs.sh` | Falsche TZ/Keyboard | P2 | v1.1 |
| i18n | WLAN Regulatory Domain | unclear | — | Illegal transmit | P2 | v1.1 |
| UI | Grafischer Rescue-Wizard | planned | `RESCUE_START_ASSISTANT_WIZARD_STATE.md` | Nur TUI heute | P2 | v1.1 |
| UI | Safe-Graphics-Modus | unclear | — | GPU-Probleme | P2 | v1.1 |
| UI | Panda auf Rescue-Stick | missing | Nur Desktop | Anfänger-Hilfe | P3 | v2 |
| Telemetrie | HW Telemetrie-ACK | partial | `rescue_network_telemetry_gate.py` | Windows-Inspect blockiert | P0 | Phase 2 |
| Telemetrie | Zone A–D Taxonomie | missing | Dev-Server MVP Klassen | DSGVO-Architekturlücke | P2 | v1.1 |
| Telemetrie | Opt-in UI auf Stick | partial | public_rescue blockiert | Consent unklar | P2 | v1.1 |
| Telemetrie | Anonymisierungspipeline K-Anonymität | missing | — | Privacy-Risiko | P3 | v2 |
| Telemetrie | Löschfristen dokumentiert | unclear | — | DSGVO | P2 | v1.1 |
| KB | Hardware-Matrix vollständig | partial | `runner_rescue_live_hardware_matrix.py` | Falsche Empfehlungen | P2 | v1.1 |
| KB | Beta→KB automatisch | planned | Dev-Server MVP §5 | Wissen stagniert | P3 | v2 |
| Tests | QEMU→HW Parität | partial | Standard-ISO ohne ttyS0 — Serial leer | Falscher Grün-Eindruck | P0 | Operator HW-Boot |
| Tests | ISO-Rebuild nach Workspace-Änderungen | partial | Build Exit 20 (sudo) | Drift 1.7.9.0 vs. Runtime 1.7.8.4 | P1 | Operator-Rebuild optional |
| Ops | USB-Write reproduzierbar | partial | Handoff RS_001_HW_BOOT_OPERATOR_HANDOFF.md | Operator-Pflicht | P0 | Operator FAT32-ESP |
| Tests | RS-001 Evidence | partial (gelb) | `RS_001_REACT_RESCUE_HARDWARE_RETEST_RESULT.md` | Fallback partial; network crash | P0 | Rebuild + Retest |
| Ops | FAT32-ESP als Standard-Writer | partial | `rescue_fat32_esp_usb_writer.py` | isohybrid-Probleme | P2 | v1.1 |
