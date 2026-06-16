# Produktfokus-Roadmap B.1

**Kampagne:** B.1 · **Version:** 1.7.15.0 · **Datum:** 2026-06-10  
**Kontext:** Architektur-Abbau Welle 3 abgeschlossen (1.7.15.0) — Fokus zurück auf Produktfunktionen.

---

## Leitprinzip

> Architektur nur noch **nebenbei**. Hauptziel: **bootfähiger Rettungsstick**, **stabile Diagnoseplattform**, **Partitionshelfer Execute** — jeweils mit **E2E-Nachweisen**.

Monolith-Abbau läuft parallel in kleinen Wellen (Backup-Execute, Rescue-Execute-Router), blockiert aber **nicht** die Produktarbeit.

---

## Priorisierte Roadmap

| Prio | Bereich | Ziel | Ampel heute | Nächster Meilenstein |
|------|---------|------|-------------|----------------------|
| **1** | **Rettungsstick bootfähig** | MSI/HW Level-6 UEFI-Boot, GRUB-Theme auf ESP, Start Assistant TUI | 🟡 | RS-001 Hardware-Retest mit Evidence |
| **2** | **WLAN stabil** | TUI-Netzwerk-Onboarding auf Referenzhardware nach Neustart | 🟡 | MSI Network Validation abschließen |
| **3** | **Telemetrie stabil** | Ingest vom Stick zum Host, kein Crash, ACK nachweisbar | 🟡 | `target_telemetry_ingest_ack: true` auf MSI |
| **4** | **Diagnoseplattform** | Telemetrieserver → Diagnoseserver (DS.1 Konzept → MVP) | 🟡 | Pipeline-Ingest + `/api/diagnostics/analyze` Hook |
| **5** | **Partitionshelfer Execute** | Writes nach Gate-Freigabe (Queue-Apply, Manifest↔Backup) | 🔴 | Manifest-Verknüpfung + Gate-Review |
| **6** | **Backup/Restore E2E** | BR-001-OFFLINE + Restore-Preview Execute | 🔴 | BR-001-OFFLINE HW-Nachweis |
| **7** | **Cloudserver Edition** | Cloud-Backup/Restore-Produktpfad | 🟡 | Nach BR-001/Restore grün |

---

## Welle 1 — Rettungsstick (R.2+)

### Ziel: Bootfähig auf Referenzhardware

| Schritt | Aufgabe | Abhängigkeit | Evidence-Ziel |
|---------|---------|--------------|---------------|
| R.2.1 | RS-001 Level-6 HW-Retest (MSI UEFI) | Operator, USB-Write (manuell) | `RS_001_HW_BOOT_PHASE3_RESULT.md` |
| R.2.2 | GRUB-Theme auf ESP verifizieren | R.2.1 | Screenshot + `isoinfo` |
| R.2.3 | WLAN-Onboarding nach Neustart | R.2.1 | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` |
| R.2.4 | Telemetrie-Ingest auf MSI | R.2.3 | `target_telemetry_ingest_ack: true` |
| R.2.5 | React-Kiosk-Entscheidung | Produktentscheidung | TUI-first vs. Browser-Stack-Doc |

### Parallel (Architektur nebenbei)

- R.2 Router-Konsolidierung Telemetry + Agent (kleine Welle)
- Deploy Rescue Execute-Routen weiter in Subrouter (D.15)

---

## Welle 2 — Diagnoseplattform (DS.1)

### Ziel: Telemetrie → Diagnose mit Nachweis

| Schritt | Aufgabe | Abhängigkeit |
|---------|---------|--------------|
| DS.1.1 | Gast→Host Report in QEMU (Fleet + Agent) | Fleet Phase 1 ✅ |
| DS.1.2 | Post-Ingest-Hook → `/api/diagnostics/analyze` | DS.1.1 |
| DS.1.3 | Session-Modell (correlation_id über Kanäle) | DS.1.2 |
| DS.1.4 | DCC Diagnose-Panel (read-only, kein LLM) | DS.1.3 |
| DS.1.5 | KB/FAQ-Verknüpfung aus EvidenceRecords | Learning Loop |

**Kein LLM in Welle 1** — erst nach stabiler Pipeline und E2E-Ingest.

---

## Welle 3 — Partitionshelfer (PH.1+)

### Ziel: Execute-Phase nach Gate-Freigabe

| Schritt | Aufgabe | Blocker |
|---------|---------|---------|
| PH.1.1 | Manifest-Pfad ↔ echtes Backup verknüpfen | Kein HW-Write |
| PH.1.2 | SMART live in UI (`use_inspect`) | Kein HW-Write |
| PH.1.3 | Storage-Discovery-Vereinheitlichung | Architektur nebenbei |
| PH.1.4 | Gate-Review: BACKUP_BEFORE_OVERWRITE, VERIFY_BEFORE_RESTORE | Backup E2E |
| PH.1.5 | Queue-Apply MVP (kontrolliert, Token) | PH.1.4 + Rescue grün |

**Writes erst nach:** Rettungsstick 🟢 + BR-001 mindestens 🟡.

---

## Welle 4 — Backup/Restore E2E

| Schritt | Aufgabe | Blocker |
|---------|---------|---------|
| BR.1 | BR-001-OFFLINE Full auf Stick | HW-Operator |
| BR.2 | Verify Deep auf Offline-Archiv | BR.1 |
| BR.3 | Restore-Preview Execute mit Evidence | BR.2 |
| BR.4 | Cross-Domain Handoff Partitions ↔ Restore | BR.3 + PH.1.1 |

---

## Welle 5 — Cloudserver Edition

Erst nach Backup/Restore E2E mindestens 🟡:

- Cloud-List/Quota readonly bereits extrahiert (B.2)
- Cloud-Write/Verify/Delete bleiben in Monolith
- Produktentscheidung WebDAV vs. S3 vs. Seafile

---

## Architektur nebenbei (nicht blockierend)

| Welle | Thema | Status |
|-------|-------|--------|
| A.4 | Monolith Welle 3 | ✅ 1.7.15.0 |
| B.2+ | Backup Execute Router | Geplant |
| D.15 | Rescue Execute Subrouter | Geplant |
| G.15 | Security/Updates aus app extrahieren | Geplant |
| R.2 | Telemetry Router Konsolidierung | Offen |

**Regel:** Keine Architektur-Welle ohne zugehörigen Produkt-Meilenstein oder explizite Freigabe.

---

## Abnahmekriterien Welle 1 (Produkt)

| Kriterium | Ampel-Ziel | Evidence |
|-----------|------------|----------|
| Rettungsstick bootet auf MSI UEFI | 🟢 | RS-001 Level 6 |
| WLAN funktioniert nach Neustart | 🟢 | Network Validation |
| Telemetrie-Ingest ACK | 🟢 | MSI Telemetry Result |
| Partitions Workbench read-only | 🟢 | Bereits ✅ |
| Diagnose-Analyse auf Telemetry-Payload | 🟡 | QEMU Gast→Host |
| Backup BR-001-OFFLINE | 🟡 | Mindestens Stick-Full |
| Restore Execute | 🔴 | Welle 4 |

---

## Beta-Bewertung (Vorläufig)

**Geschlossene Beta:** noch **nicht empfohlen**.

**Blocker:**

1. Rettungsstick HW-Level-6 nicht grün
2. BR-001-OFFLINE rot
3. Restore Execute fehlt komplett
4. Telemetrie E2E-Ingest nicht nachgewiesen

**Beta-fähig wenn:** Prio 1–3 grün + mindestens BR-001 🟡 + Diagnose-MVP 🟡.

---

## Referenzen

- `docs/evidence/rescue/RESCUE_STATUS_AUDIT_R2.md`
- `docs/evidence/partition/PARTITION_HELPER_STATUS_AUDIT_PH1.md`
- `docs/architecture/DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md`
- `docs/evidence/E2E_GAP_ANALYSIS_E2E1.md`
- `docs/architecture/MONOLITH_DECOMPOSITION_ROADMAP.md`
