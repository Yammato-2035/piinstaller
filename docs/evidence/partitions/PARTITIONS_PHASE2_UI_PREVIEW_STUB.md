# Partitions Phase 2 – UI Preview Stub (Evidence)

**Datum:** 2026-05-24  
**Basis-HEAD:** `4cf5cd7` (Backend Phase 2)  
**UI-Commit:** siehe `git log -1`

---

## Runtime (Smoke zum Zeitpunkt der UI-Arbeit)

| Prüfung | Ergebnis |
|---------|----------|
| `check-runtime-deploy-gate.sh` | teils Exit 14 (Deploy-Drift Workspace↔/opt) |
| `GET /openapi.json` | **200** |
| `/api/partitions/*` | **8 Pfade** in Runtime |
| `hardstop-preview?target_device=/dev/sdb` | **200**, `write_allowed: false` |

Hinweis: Offizieller `deploy-to-opt.sh` + `systemctl restart` durch Operator empfohlen, falls Gate rot.

---

## Neue/geänderte Frontend-Dateien

| Datei | Änderung |
|-------|----------|
| `frontend/src/api/partitionApi.ts` | Phase-2 API-Client |
| `frontend/src/components/partition/PartitionSafetyPreviewPanel.tsx` | Read-only Vorschau-Panel |
| `frontend/src/pages/PartitionManager.tsx` | Integration bei Partition-Auswahl |
| `frontend/src/locales/de.json` | `partition.phase2.*` |
| `frontend/src/locales/en.json` | `partition.phase2.*` |

---

## UI-Verhalten

- Bei Auswahl einer Partition: automatisch Hardstop-, Manifest- und Restore-Handoff-Preview laden
- Button „Sicherheitsvorschau aktualisieren“ (read-only Refresh)
- Keine Schreib-, Format-, Lösch- oder Apply-Buttons in Phase-2-Panel
- `ActionQueueBar` / Phase-1-Scan unverändert

---

## Schreibschutz

- UI zeigt `write_allowed: false` / Schreibzugriff blockiert
- Keine neuen Write-API-Aufrufe
- Queue/apply nicht aktiviert

---

## i18n

- Keys unter `partition.phase2.*` (DE mit Umlauten, EN parallel)
- Code-Labels unter `partition.phase2.code.*`

---

## Tests / Build

```bash
npm --prefix frontend run build
PYTHONPATH=backend backend/venv/bin/python3 -m pytest \
  backend/tests/test_partitions_api_v1.py \
  backend/tests/test_partitions_phase2_safety_contracts_v1.py -q
```

OpenAPI-Runtime-Assert: 8 Partition-Pfade inkl. Phase 2.

---

## tkinter

Unverändert unter `apps/partitionshelfer/`.
