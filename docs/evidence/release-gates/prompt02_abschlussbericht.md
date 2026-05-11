# Abschlussbericht – Prompt 2 (Blocker-Inventar), **erneute Ausführung**

**Ausführung:** 2026-05-11T21:15:00Z  
**Spezifikation:** `docs/cursor/PROMPT_02_BLOCKER_INVENTORY.md`  
**Maschinenlesbar:** `blocker_inventory.json` · **Pytest-Snapshot:** `current_failures.json` · **Ports/Services:** `runtime_inventory.json`

## Phase 1 – Testbestand (kurz)

| Artefakt | Befund |
|----------|--------|
| Testdateien `backend/tests` | **190** Dateien (`test_*.py`) |
| Testdoku (Stichprobe) | `docs/testing/*_TEST_MATRIX.md`, `docs/developer/BACKUP_RESTORE_STABILITY_TEST_MATRIX.md`, `docs/knowledge-base/deploy/DEPLOY_HARDWARE_GATE.md` |
| Evidence-Verzeichnisse | `docs/evidence/` inkl. `release-gates/`, `hardware/`, `backup-restore/`, `rescue-stick/`, `website/` |
| Diagnostik-Seeds | `data/diagnostics/evidence/*.json` — **38** Dateien, nach Coercion alle **`EvidenceRecord`-valide** (`diagnostics_evidence_seed_audit_2026-05-11.json`) |

## Phase 2 – Fehler / Risiken

| Kategorie | Befund |
|-----------|--------|
| Fehlschlagende Tests (lokal) | **0** (`PI_INSTALLER_DEV=1 PYTHONWARNINGS=default python -m pytest tests/ -q --tb=no` → 1526 passed, 2 warnings, ~19 s) |
| Fehlende / E2E-offene Tests | Backup→Verify→Restore→Boot auf **freigegebenem Medium** nicht als abgeschlossene Evidence dokumentiert |
| Unstabile / umgebungsabhängige Bereiche | u. a. `/media`-Pfade (bekannt; Tests nutzen wo nötig `/tmp`-Isolation) |
| Legacy pi-installer ↔ setuphelfer | weiter **gelb** (`legacy_inventory.json`) |
| Service-/Port-Raster | weiter **gelb** (`runtime_inventory.json`, u. a. 8000 / 3001 / 5173 / 8010) |
| Mount/Permission | weiter **gelb** (`storage_permission_inventory.json`) |

## Phase 3 – Blocker-Klassifikation (Ampel)

### P0

| ID | Kurz |
|----|------|
| **P0-HW-E2E** | Kein vollständiger dokumentierter Hardware-Nachweis Backup → Verify → Restore → Boot auf freigegebenem Medium. |

### P1

| ID | Kurz |
|----|------|
| **P1-CI-EVIDENCE** | Kein verlinkter grüner GitHub-Actions-Gesamtlauf in Evidence. |
| **P1-RESCUE-RS** | Rescue-Stick / RS-* Runtime-Evidence und Operator-Abnahme ausstehend (Unit-Pfad lokal grün). |

### P2

| ID | Kurz |
|----|------|
| **P2-WEB-WT** | Live-Website vs. WT-* / Statusseite nicht abgenommen. |
| **P2-LEGAL** | Impressum/Datenschutz/Affiliate nur Repo-Entwurf. |

### P3

| ID | Kurz |
|----|------|
| **P3-MONOLITH** | DOMAIN_BOUNDARIES / späterer Prompt 5. |
| **P3-CLOUD** | Cloudserver-Edition — schwarz geparkt. |

## Phase 4 – Aktualisierte Outputs (STRICT: Doku/Evidence only)

- `docs/roadmap/STATUS_MATRIX.md` — Standzeile auf diese Ausführung bezogen  
- `docs/evidence/release-gates/current_failures.json` — Snapshot  
- `docs/evidence/release-gates/runtime_inventory.json` — Zeitstempel Prompt-2-Refresh  
- `docs/evidence/release-gates/blocker_inventory.json` — Inventar + `prompt02_rerun`  
- `docs/evidence/release-gates/test_inventory.json` — `pytest_snapshot`  
- `docs/evidence/release-gates/pytest_failures_summary_2026-05-11.txt` — Textzusammenfassung  
- `docs/evidence/release-gates/diagnostics_evidence_seed_audit_2026-05-11.json` — Seed-Audit  

## Empfohlene Reihenfolge (unverändert inhaltlich)

1. P0 **HW-E2E** nach Matrix/Runbook.  
2. **CI-Evidence** verlinken (P1-CI-EVIDENCE).  
3. **Rescue-Stick / RS-*** (P1-RESCUE-RS).  
4. Website/Legal (P2).  
5. Monolith-Audit (P3).

---

*STRICT MODE eingehalten: keine Feature-Implementierung, keine Refactors, keine Löschoperationen, keine echten Restores, keine Systempfad-Veränderung.*
