# PI-RS-MSI-RETEST-001 — MSI GE63 Raider Retest Checkliste

Stand: 2026-07-10
Sprint: Planung und Payload-Entscheidung (kein Operator-Boot in diesem Sprint)

## Testgerät

| Feld | Wert |
|------|------|
| Modell | MSI GE63 Raider RGB 8RF |
| Board | MS-16P5 |
| GPU | NVIDIA GTX 1070 + Intel iGPU |
| WLAN | Intel AC9560 |
| LAN | Killer E2500 |
| BIOS (letzter Boot-Log) | E16P5IMS.109 |

## Stick-/Payload-Stand (vor Retest dokumentieren)

| Quelle | Version | Hinweis |
|--------|---------|---------|
| `SETUPHELFER/setuphelfer/rescue/version.json` | **1.10.0.12** | `squashfs_sha256` = Baseline |
| `SETUP_LOGS/.../api-version.json` | **1.10.0.12** | Letzter MSI-Lauf |
| Workspace `config/version.json` | **1.9.19.4** | Drift bewusst dokumentieren |

**Kein USB-Update / kein Repack in PI-RS-MSI-RETEST-001.**

## Vor Boot (Operator)

- [ ] Stick-Version und Payload-SHA256 notieren (Foto/Screenshot)
- [ ] `SETUP_LOGS` Partition frei genug (55G vfat)
- [ ] Keine produktiven Telemetry Sends planen
- [ ] Netzwerk optional; wenn aktiv: nur Lab/localhost/Preview-Kontext
- [ ] `production_ready=false`, `preview_only=true` bestätigen

## Zu prüfen (Boot-Retest)

1. [ ] Bootmenü (GRUB) erscheint
2. [ ] TUI startet (`setuphelfer_mode=text`)
3. [ ] GUI-Fallback / GUI-Start (`setuphelfer_kiosk=0`, optional GUI-Watchdog)
4. [ ] Backend `/api/version` erreichbar (127.0.0.1:8000)
5. [ ] Storage Discovery
6. [ ] Disk Inventory
7. [ ] Hardware Inventory
8. [ ] PCIe/AER/Killer-E2500-Warnungen (bekanntes MSI-Thema)
9. [ ] WLAN-Erkennung Intel AC9560
10. [ ] `SETUP_LOGS` Persistenz (diagnostics/latest, evidence)
11. [ ] Operator Steps Logging (`operator-steps.jsonl` falls vorhanden)
12. [ ] Telemetry Preview bleibt `preview_only` (kein Produktivsend)
13. [ ] Offline Queue Verhalten (deferred, kein Crash)
14. [ ] Keine Secrets/Rohlogs in exportierten Artefakten
15. [ ] Kein produktiver Send
16. [ ] Kein Auto-Fix / keine Reparatur
17. [ ] Kein Remote Command
18. [ ] Screenshots/Fotos bei UI-Abweichungen

## Nach Boot

- [ ] `SETUP_LOGS` mounten und Evidence sichern (siehe Import-Plan)
- [ ] `setuphelfer/diagnostics/latest/00-meta.txt` prüfen
- [ ] `setuphelfer/evidence/msi-rs011b/api-version.json` prüfen
- [ ] `storage-discovery.json`, `disk-discovery.json` prüfen
- [ ] `operator-steps.jsonl` prüfen (falls erzeugt)
- [ ] Retest-Ergebnis: passed / partial / failed / repack_required

## Grenzen

- Kein USB-Schreiben ohne separates Operator-Go
- Keine Reparatur auf dem MSI
- Cross-Repo Diagnostics nur Preview/localhost (PI-RS-TEL-003)
