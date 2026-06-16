# E2E Gap Analysis E2E.1

**Kampagne:** B.1 · **Version:** 1.7.15.0 · **Datum:** 2026-06-10  
**Modus:** Evidence-Inventar (kein Runtime-Test)

---

## Ampel-Legende

| Ampel | Bedeutung |
|-------|-----------|
| 🟢 | Vollständiger Nachweis (Runtime/HW/API-Smoke mit `evidence_complete`) |
| 🟡 | Teilnachweis (Lab, Unit, plan-only, blockierte Operator-Schritte) |
| 🔴 | Fehlend, Template-only oder Release-Gate blockiert |

---

## Gesamtübersicht

| Domain | Ampel | Kritischster fehlender Nachweis |
|--------|-------|--------------------------------|
| **Rettungsstick / Rescue** | 🟡 | HW Level-6 UEFI-Boot + Gast→Host-Telemetrie |
| **Backup** | 🔴 | BR-001-OFFLINE Full auf Stick |
| **Restore** | 🔴 | Jeder Execute-/HW-Restore-Lauf |
| **Partitionshelfer** | 🟢 | Write/HW-Partitionierung (bewusst offen) |
| **Diagnoseserver / Telemetry** | 🟡 | QEMU/Stick→Host-Ingest E2E |

---

## 1. Rettungsstick / Rescue

### Vorhandene Nachweise 🟢/🟡

| Nachweis | Evidence | Ampel |
|----------|----------|-------|
| Controlled ISO-Build erfolgreich | `RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md` | 🟢 |
| QEMU-Boot visuell teilweise | `RESCUE_DEVELOPER_ISO_QEMU_BOOT_SMOKE_RESULT.md` | 🟡 |
| RS-001 Stick-Acceptance L1–4 | `RS_001_STICK_ACCEPTANCE_RESULT.md` | 🟢 |
| ISO-Gate-Tests | `rescue_iso_controlled_gate_test_results_latest.json` | 🟢 |
| Fleet Phase 1 API | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` | 🟢 |
| Payload-Fix Vorbereitung/Build-Tree | `PAYLOAD_FIX_*` | 🟡 |
| Grafische Assets Validation | `test_rescue_graphical_assets_v1.py` | 🟢 |

### Fehlende Nachweise 🔴

| Nachweis | Grund | Ampel |
|----------|-------|-------|
| Lab Acceptance Runbooks (7×) | Alle `missing` in `LAB_ACCEPTANCE_REPORT.json` | 🔴 |
| HW Level-6 UEFI-Boot (MSI) | `RS_001_REACT_RESCUE_HARDWARE_RETEST_RESULT.md` pending | 🔴 |
| QEMU Guest-Agent-Smoke | `agent_send_failed`, kein Guest-Report | 🔴 |
| USB-Write + MSI-Telemetrie-Ingest | `target_telemetry_ingest_ack: false` | 🔴 |
| RS-001…RS-008 Testmatrix | Größtenteils Template/rot | 🔴 |
| `release-gates/rescue_report.json` | Rot | 🔴 |
| React-Kiosk auf Live-OS | Kein Browser im SquashFS | 🔴 |

---

## 2. Backup

### Vorhandene Nachweise 🟡

| Nachweis | Evidence | Ampel |
|----------|----------|-------|
| BR-001 extern (Daten + Verify Deep) | `BR-001.json`, `BR-001-external-validation-2026-05-15.md` | 🟡 |
| BR-001 Diagnostik/Runbooks | Mount, systemd, package_activity | 🟡 |
| Storage-IO-Stabilität 15 GiB | passed | 🟢 |
| Unit-/CI-Tests | `release-gates/test_inventory.json` | 🟢 |
| Domain-Audit B.2 readonly | `BACKUP_READONLY_ROUTER_B2.md` | 🟢 |

### Fehlende Nachweise 🔴

| Nachweis | Grund | Ampel |
|----------|-------|-------|
| **BR-001-OFFLINE** Full auf Rettungsstick | `backup_restore_release_gate.json` rot | 🔴 |
| Full-Root-Live | package_activity, write_io, tar fehlgeschlagen | 🔴 |
| BR-002 … BR-010 | Templates/blocked | 🔴 |
| BR-004/005 Verify-Kette Offline-Archiv | Offen | 🔴 |
| HW-E2E Backup-Kette | Explizit dokumentiert als offen | 🔴 |

---

## 3. Restore

### Vorhandene Nachweise 🟡

| Nachweis | Evidence | Ampel |
|----------|----------|-------|
| Restore-Preview-Handoff plan-only | `rescue_phase_c4_restore_preview_handoff_*.json` | 🟡 |
| Partitions API `restore-handoff-preview` | `PARTITIONS_FINALIZATION_RESULT.md` | 🟢 |
| Unit-Tests | `test_partitions_restore_handoff_preview_v2` | 🟢 |
| Deploy-Runner Orchestrator | plan-only | 🟡 |

### Fehlende Nachweise 🔴

| Nachweis | Grund | Ampel |
|----------|-------|-------|
| Ausgeführter Restore (API oder HW) | Kein Execute-Lauf dokumentiert | 🔴 |
| `handoff/rescue_restore_preview_result.json` | Fehlt in runtime-results/handoff | 🔴 |
| HW-Restore auf Zielmedium | Blockiert durch Gates | 🔴 |
| Cross-Domain Backup→Verify→Restore | Release-Gate offen | 🔴 |

---

## 4. Partitionshelfer

### Vorhandene Nachweise 🟢

| Nachweis | Evidence | Ampel |
|----------|----------|-------|
| Phase-1-Runtime | `PARTITIONS_PHASE1_RUNTIME_VALIDATION.md` | 🟢 |
| Browser-UI-Smoke | `PARTITIONS_FINAL_BROWSER_UI_SMOKE.md` | 🟢 |
| Workbench Runtime | `PARTITIONSHELFER_WORKBENCH_RUNTIME_ACCEPTANCE.md` | 🟢 |
| Hardstop/Manifest/Restore-Preview | API read-only, `write_allowed=false` | 🟢 |

### Fehlende Nachweise 🟡/🔴

| Nachweis | Grund | Ampel |
|----------|-------|-------|
| Phase 2 Write/Queue-Apply | Bewusst nicht ausgeführt | 🟡 |
| HW-Partitionierung | format/delete/parted | 🔴 |
| E2E mit echtem Backup/Restore-Start | Nicht über Partitions-UI | 🔴 |

---

## 5. Diagnoseserver / Telemetry

### Vorhandene Nachweise 🟢/🟡

| Nachweis | Evidence | Ampel |
|----------|----------|-------|
| Dev-Server MVP lokal | `DEV_SERVER_MVP_RUNTIME_ACCEPTANCE.md` | 🟢 |
| Rescue-Telemetry-Ingest Workspace | `RESCUE_TELEMETRY_INGEST_SEPARATE_FROM_DCC_RESULT.md` | 🟢 |
| Fleet Phase 1 Live | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` | 🟢 |
| Telemetry-Proxy/Health Dev-Laptop | `RESCUE_MSI_TELEMETRY_LAN_PROXY_FINALIZATION_RESULT.md` | 🟡 |
| DCC Release-Baseline | `DCC_LIVE_ACCEPTANCE_RELEASE_BASELINE.md` | 🟡 |

### Fehlende Nachweise 🔴/🟡

| Nachweis | Grund | Ampel |
|----------|-------|-------|
| Gast→Host Dev-Server-Report (QEMU/ISO) | `guest_report_missing`, `agent_send_failed` | 🔴 |
| MSI-Telemetrie-Ingest | `target_telemetry_ingest_ack: false` | 🔴 |
| Live-Ingest nach Backend-Restart | Offen | 🟡 |
| WoL zuverlässig | `RESCUE_TELEMETRY_WOL_DEVSERVER_CHECK.md` unsicher | 🟡 |
| `runtime-results/dev-server/` Artefaktbaum | Nicht vollständig im Repo | 🟡 |

---

## 6. Cross-Domain E2E-Kette (fehlend)

Die folgende Kette hat **keinen grünen End-to-End-Nachweis**:

```
Rettungsstick booten
  → Netzwerk/WLAN stabil
    → Telemetrie-Ingest zum Host
      → Dev-Server-Report / Diagnose-Analyse
        → Backup auf externes Ziel (BR-001-OFFLINE)
          → Verify Deep
            → Restore-Preview Execute
              → Partition-Plan mit Handoff
```

**Jeder Schritt einzeln:** teilweise 🟡 — **Kette gesamt:** 🔴

---

## 7. Empfohlene E2E-Nachweise (Priorität)

| Prio | Nachweis | Domäne |
|------|----------|--------|
| P0 | RS-001 Level-6 HW-Boot + WLAN + Telemetrie-Ingest | Rescue |
| P0 | BR-001-OFFLINE Full auf Stick + Verify | Backup |
| P1 | Gast→Host Report in QEMU (Fleet + Agent) | Telemetry |
| P1 | Restore-Preview Execute mit Evidence | Restore |
| P2 | Partition Write nach Gate-Freigabe (HW) | Partitions |
| P2 | Diagnose-Analyse auf Telemetry-Payload | Diagnoseserver |

---

## Referenzen

- `docs/evidence/README.md` (Evidence-Schema)
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json`
- `docs/evidence/release-gates/backup_restore_release_gate.json`
- `docs/evidence/rescue/RESCUE_STICK_GAP_LIST.md`
- `docs/evidence/backup/BACKUP_DOMAIN_AUDIT_B1.md`
