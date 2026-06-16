# Diagnoseserver-Architektur DS.1

**Kampagne:** B.1 · **Version:** 1.7.15.0 · **Datum:** 2026-06-10  
**Status:** Konzept / Inventar — **keine Implementierung**

---

## 1. Zielbild

Der **Telemetrieserver** soll zum **Diagnoseserver** weiterentwickelt werden: ein zentraler, profil-sicherer Dienst, der lokale und remote Signale sammelt, mit strukturierter Evidence und Wissensbasis korreliert, und Entwickler sowie Endanwender bei der Fehleranalyse unterstützt — ohne Backup/Restore/Write-Aktionen.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Diagnoseserver (Ziel DS.1+)                   │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ Ingest Plane │ Session Plane│ Analysis Plane│ Knowledge Plane  │
│ (Telemetry)  │ (Runs/Agents)│ (Matcher)    │ (KB/FAQ/Evidence)│
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬─────────┘
       │              │              │                │
  Rescue Telemetry  Fleet/QEMU   /api/diagnostics   KB + FAQ
  Dev-Server      Rescue-Agent  interpret_v1       WISSENSDATENBANK
  Windows Inspect Rescue-Remote dev-diagnostics    Learning Loop
```

---

## 2. Ist-Inventar

### 2.1 Telemetrie

| Modul | Pfad | Fähigkeit | Profil |
|-------|------|-----------|--------|
| Rescue Telemetry Ingest | `core/rescue_telemetry_ingest.py`, `rescue_telemetry/routers.py` | Envelope, HMAC, Privacy, Queue/Ack | Release ✅ |
| Rescue Telemetry Tasks | `core/rescue_telemetry_tasks.py` | Allowlist-Task-Pull (collect_logs, network_check, …) | Release ✅ |
| Rescue LAN Proxy | `core/rescue_telemetry_lan_proxy.py` | HTTP-Forwarder Stick→Host | Dev/Lab |
| Rescue Network Gate | `core/rescue_network_telemetry_gate.py` | Gate-Status aus Evidence | Plan/Gate |
| Backup Telemetry | `core/backup_telemetry.py` | status.json Spiegelung (lokal) | Produkt |
| Fleet Session | `core/fleet_session_state.py`, `fleet/routers.py` | QEMU/Lab Heartbeat, Serial, Evidence | Dev |

**Trennung dokumentiert:** Rescue-Telemetrie ≠ DCC ≠ Dev-Server (`LOCAL_LAB_TELEMETRY.md`).

### 2.2 Agenten

| Agent | Pfad | Fähigkeit | Status |
|-------|------|-----------|--------|
| Development Agent | `devserver_agent/` (cli, collector, spool) | Read-only Collector, Auto-Upload | MVP ✅ |
| Rescue Agent | `rescue_agent/` | In-Memory-Stub, Pairing-Stub, E2EE-Stub | Phase-1 Stub |
| Rescue Remote | `rescue_remote/` | Allowlisted Runbooks, JSONL-Persistenz | local_lab |

### 2.3 DCC / Development Control Center

| Modul | Pfad | Rolle |
|-------|------|-------|
| `dcc_status_facade` | `core/dcc_status_facade.py` | Kanonische read-only Aggregation |
| `dev_dashboard` | `core/dev_dashboard.py` | Module-Registry, Deploy-Drift, Gates |
| `dev_dashboard_status_service` | Trennt Rescue-Telemetry von DCC | Capability-Gate |
| `dev_dashboard_recent_evidence` | Whitelist-Scan `docs/evidence/*` | Feed |
| Readonly Router | `api/routes/dev_dashboard_readonly.py` | 10+ GET |
| Frontend | `components/dev-dashboard/` (46 Panels) | Rescue, Fleet, Evidence, AI-Export |

### 2.4 Development Server

| Modul | Pfad | Fähigkeit |
|-------|------|-----------|
| Dev Server Router | `devserver/routers.py` | Health, Nodes, Reports, Ingest, Actions |
| Ingest | `devserver/ingest.py` | Token-Auth, Redaction |
| Storage | `devserver/storage.py` | Dateibasiert unter `docs/evidence/runtime-results/dev-server/` |
| SSH Read-only | `ssh_readonly.py` | Allowlisted Profile |
| Prompt Candidates | `prompt_candidates.py` | Report-Warnings → Draft-Task (kein LLM) |

### 2.5 Evidence-System

| Schicht | Pfad | Fähigkeit |
|---------|------|-----------|
| Strukturierte Evidence | `data/diagnostics/evidence/*.json` | `EvidenceRecord` (DIAG-1.1), 40+ Records |
| Evidence Store | `core/diagnostics/evidence_store.py` | Laden, Aggregation |
| Repo-Evidence | `docs/evidence/` | Markdown/JSON-Berichte, Gates |
| Dev Diagnostic Export | `core/dev_diagnostic_export.py` | Redacted Export Fleet/QEMU |
| Learning Loop | `docs/knowledge-base/diagnostics/LEARNING_LOOP.md` | Evidence → Katalog/FAQ/KB |

### 2.6 Diagnose-Engines

| Engine | API | Status |
|--------|-----|--------|
| Diagnostics Core | `/api/diagnostics/analyze`, `/catalog` | Kanonisch, ~30+ DiagnosticCase-IDs |
| Diagnosis Interpreter | `POST /api/diagnosis/interpret` | Legacy regelbasiert |
| Dev Diagnostics | `/api/dev-diagnostics/*` | Lab-Export read-only |

### 2.7 Wissensbasis

| Bereich | Pfad | Umfang |
|---------|------|--------|
| Host-Wissensdatenbank | `docs/host-env/WISSENSDATENBANK.md` | KB-001…014 |
| Knowledge Base | `docs/knowledge-base/` (~299 Dateien) | diagnostics, rescue, development, … |
| FAQ | `docs/faq/` (23 Dateien) | DE/EN-Paare |

---

## 3. Zielarchitektur — fünf Diagnosemodi

### 3.1 Lokale Diagnose

**Heute:** Drei parallele Engines (`/api/diagnostics`, `/api/diagnosis/interpret`, System-Status-Facades).

**Ziel DS.1+:**

- Ein Analyse-Entry-Point (`Diagnoseserver.analyze(signals)`)
- Legacy-Interpreter als Adapter, nicht Parallel-Logik
- Lokaler Signal-Bus: systemd, Ports, Logs, Backup-Telemetry → normalisierte `signals`
- Optional: jeder `/analyze`-Treffer erzeugt `EvidenceRecord`

### 3.2 Remote-Diagnose

**Heute:** Drei getrennte Kanäle (Rescue-Telemetry, Dev-Server-Ingest, Fleet-Sessions).

**Ziel DS.1+:**

- Einheitliches **Session-/Run-Modell** über Kanäle hinweg (`session_id`, `boot_id`, `run_id`)
- Rescue-Agent: persistenter Pairing-State, Stick↔Server-Vertrauen
- Rescue-Remote: Job-Pull mit Ergebnis-Feed in Diagnosekatalog
- Release-sichere Exposure-Matrix ohne Dev-only-Leaks

### 3.3 KI-gestützte Fehleranalyse

**Heute:** Kein Backend-LLM; `prompt_candidates.py` und `cursor-meta-prompt` = Text-Stubs.

**Ziel DS.1+:**

- Kontrollierter Kontext: Katalog + redacted Telemetry + Evidence
- RAG-Vorbereitung: Index über KB/FAQ/Evidence (`DIAGNOSIS_DATA_MODEL.md`)
- Server-seitige Safety: `no backup`, `no restore`, `no write` durchgesetzt
- UI: interaktiver Diagnose-Chat mit Evidence-Grounding (nach MVP)

### 3.4 Wissensdatenbank

**Heute:** Markdown-Dateien, manuelle `related_docs`/`related_faq` im Katalog.

**Ziel DS.1+:**

- Zentraler KB-Index-API mit Versionierung und Such-Endpoint
- `WISSENSDATENBANK.md` verknüpft mit `DiagnosticCase` und Telemetry-Symptomen
- Learning Loop automatisiert: Evidence ohne KB/FAQ-Update → CI-Warnung
- i18n-Vollständigkeit als Qualitätsgate

### 3.5 FAQ

**Heute:** 23 FAQ-Dateien, DCC Docs-Consistency-Scan.

**Ziel DS.1+:**

- FAQ-Generierung aus bestätigten `EvidenceRecord`s (human-reviewed)
- Maschinenlesbare FAQ-Refs im Diagnosekatalog
- DE/EN-Pair-Vollständigkeit als Release-Gate

### 3.6 Telemetrie-Pipeline

**Heute:** File-basierte Queues (telemetry-ingest, fleet JSONL, dev-server storage).

**Ziel DS.1+:**

```
Ingest → Normalize → Enrich → Analyze → Store → Notify
         (Envelope)   (Profile)  (Matcher) (Evidence) (DCC/UI)
```

- Cross-Channel-Correlation-ID
- Post-Ingest-Hook: automatisches `/api/diagnostics/analyze`
- Zentrales Health: Pipeline-Lag, Queue-Tiefe, letzte Diagnose
- Router-Konsolidierung R.2: gemeinsame Telemetry-Ingest-Facade

---

## 4. Modul-Cluster (konzeptionell)

| Cluster | Bestehende Bausteine | DS.1-Ziel |
|---------|---------------------|-----------|
| **Ingest Plane** | rescue_telemetry_ingest, devserver/ingest, fleet | Normalisiertes Envelope |
| **Session Plane** | fleet, rescue_remote, rescue_agent | Ein Run/Session-Modell |
| **Analysis Plane** | core/diagnostics/*, interpret_v1 | Ein Matcher + Legacy-Adapter |
| **Evidence Plane** | data/diagnostics, docs/evidence | Write-on-learn |
| **Knowledge Plane** | KB, FAQ, WISSENSDATENBANK | Index + RAG-Vorbereitung |
| **Presentation Plane** | DCC, dev_diagnostics, AIExportPanel | Local + Remote UI |
| **Governance Plane** | install_profile, route_exposure | Release-sichere Matrix |

---

## 5. Integrationsmatrix

| Quelle | Ziel | Mechanismus |
|--------|------|-------------|
| devserver_agent | Dev Server | HTTP ingest |
| Rescue-Stick / Windows | Rescue Telemetry | HTTP ingest (+ LAN-Proxy) |
| Fleet/QEMU | Dev Diagnostics | Session JSONL → Export |
| Rescue Remote | Rescue Remote Jobs | Register/Heartbeat/Pull |
| Evidence JSON | Diagnostics Catalog | `evidence_summary_map()` |
| System Status Facades | First-Level-Diagnose | `/api/system/status` |
| DCC | Alle read-only Quellen | `dcc_status_facade` |

---

## 6. Gaps (priorisiert)

| Prio | Gap | Auswirkung |
|------|-----|------------|
| P0 | Kein einheitlicher Diagnoseserver-Prozess | Drei APIs, drei ID-Namespaces |
| P0 | Gast→Host Telemetry-Ingest E2E fehlt | Rescue-Diagnose unvollständig |
| P1 | Rescue-Agent Stub (In-Memory) | Remote-Diagnose nicht produktiv |
| P1 | Keine Pipeline-Orchestrierung | Manuelle Evidence-Pflege |
| P1 | R.2 Router-Konsolidierung offen | Wartungsaufwand |
| P2 | Kein LLM/RAG | KI-Diagnose nur als Cursor-Stub |
| P2 | KB nicht maschinenlesbar indexiert | Manuelle `related_docs` |

---

## 7. Abgrenzung (Safety)

- Diagnoseserver: **read-only** — keine Backup-, Restore-, Partition-Write-Aktionen
- Release-Profil: Telemetry erlaubt; Rescue-Agent/Remote/DCC blockiert
- Redaction vor Persistenz in allen Ingest-Kanälen
- Profil-Trennung: `install_profile`, `route_exposure`, `developer_capability`

---

## 8. Referenzen

- `docs/knowledge-base/diagnostics/DIAGNOSIS_ARCHITECTURE.md`
- `docs/knowledge-base/diagnostics/EVIDENCE_MODEL.md`
- `docs/knowledge-base/diagnostics/LEARNING_LOOP.md`
- `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md`
- `docs/knowledge-base/development/LOCAL_LAB_TELEMETRY.md`
- `docs/knowledge-base/rescue/RESCUE_AGENT_AND_DEVSERVER.md`

---

## Fazit

Das Repo hat bereits eine **mehrschichtige Diagnose-Landschaft**. Für den Diagnoseserver fehlt vor allem **Vereinheitlichung** (Pipeline, Session-Modell, ein Analyse-Entry-Point) und die **Brücke zu KI/RAG** — bei klarer Beibehaltung der Safety-Gates und Profil-Trennung.
