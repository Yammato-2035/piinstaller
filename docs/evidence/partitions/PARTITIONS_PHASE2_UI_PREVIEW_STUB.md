# Partitions Phase 2 – UI Preview Stub (Evidence)

**Datum:** 2026-05-24  
**Basis-HEAD:** `4cf5cd7` (Backend Phase 2)  
**UI-Commit:** `395ba6f` (`feat(partitions): add read-only phase 2 safety preview UI`)

---

## Runtime (Smoke zum Zeitpunkt der UI-Arbeit)

| Prüfung | Ergebnis |
|---------|----------|
| `check-runtime-deploy-gate.sh` | teils Exit 14 (Deploy-Drift Workspace↔/opt) |
| `GET /openapi.json` | **200** |
| `/api/partitions/*` | **8 Pfade** in Runtime |
| `hardstop-preview?target_device=/dev/sdb` | **200**, `write_allowed: false` |

Hinweis: Offizieller `deploy-to-opt.sh` + `systemctl restart` durch Operator empfohlen, falls Gate rot.

## Runtime-Abnahme nach Push + Deploy (2026-05-24)

| Prüfung | Ergebnis |
|---------|----------|
| `git push origin main` | **395ba6f** auf `origin/main` |
| `sudo ./scripts/deploy-to-opt.sh` (Operator) | abgeschlossen, Services neu gestartet |
| `check-runtime-deploy-gate.sh` | **Exit 0** |
| `frontend/dist` unter `/opt` | gebaut (vite), enthält Phase-2-UI-Strings |
| UI HTTP (Port 3001) | **200** |
| API-Smoke-Kette (wie UI) | scan OK, hardstop OK, manifest unavailable OK |

---

## Runtime Gate Nachtrag nach Push 395ba6f

- Commit **395ba6f** wurde erfolgreich nach `origin/main` gepusht.
- **Runtime-Gate** nach Operator-/dist-Sync: **Exit 0** (`check-runtime-deploy-gate: OK`).
- **Phase-2-API-Pfade** in Runtime vorhanden:
  - `/api/partitions/scan`
  - `/api/partitions/safety-check`
  - `/api/partitions/queue`, `/api/partitions/queue/{action_id}`, `/api/partitions/queue/apply`
  - `/api/partitions/hardstop-preview`
  - `/api/partitions/manifest-layout-preview`
  - `/api/partitions/restore-handoff-preview`

### Phase-2-UI-Bundle in `/opt` aktiv

| Artefakt | Pfad / Wert |
|----------|-------------|
| JS-Bundle | `index-e3NQHPXg.js` |
| CSS | `index-Cj0u_gkp.css` |
| Einstieg | `/opt/setuphelfer/frontend/dist/index.html` → verweist auf obiges Bundle |

**Bundle enthält (String-Check):**

- `Sicherheitsvorschau`
- `hardstop-preview`

### API-Smoke (read-only)

| Aufruf | Ergebnis |
|--------|----------|
| `GET /api/partitions/scan` | **3** Disks |
| `GET /api/partitions/hardstop-preview?target_device=/dev/sda1` | **HTTP 200**, `review_required` / `yellow`, `write_allowed=false` |
| `POST /api/partitions/manifest-layout-preview` (`manifest=null`) | `unavailable`, `write_allowed=false` |

### UI-Smoke

| Prüfung | Ergebnis |
|---------|----------|
| `http://127.0.0.1:3001/` | **HTTP 200** |
| Browser | Seite **„Partitionen“** → Partition wählen → Panel **„Sicherheitsvorschau“** |

### Schreibschutz

- Keine Format-, Lösch- oder Apply-Aktion in der Phase-2-Vorschau.
- **Queue/apply** bleibt Stub (Phase 2).
- **`write_allowed=false`** bleibt in API und UI sichtbar.

### Formale Einschränkung (historisch, vor Deploy 2026-05-24 17:24)

**Der vollständige offizielle Deploy** über
`sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`
**stand zunächst aus.** Der Runtime-Gate-Lauf war **grün**, der Phase-2-UI-**dist**-Sync erfolgte vorübergehend als **Workaround** (`index-e3NQHPXg.js`). **Ersetzt** durch formale Deploy-Abnahme unten.

---

## Formale Deploy-Abnahme nach b647840

**Datum/Zeit:** 2026-05-24 (nach Operator-Lauf `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`)

| Prüfung | Ergebnis |
|---------|----------|
| Offizieller `deploy-to-opt.sh` | **ausgeführt** (Operator, Terminal-Log: Deploy abgeschlossen) |
| Manueller dist-Sync in dieser Phase | **nein** |
| `check-runtime-deploy-gate.sh` | **Exit 0** |
| `setuphelfer-backend.service` | **active** |
| `setuphelfer.service` (Web-UI) | **active** |
| OpenAPI Partitions-Pfade | **8/8** (inkl. hardstop, manifest-layout, restore-handoff) |
| `GET /api/partitions/scan` | **200**, 3 Disks |
| `GET /api/partitions/hardstop-preview?target_device=/dev/sda1` | **200**, `review_required`/`yellow`, `write_allowed=false` |
| `POST /api/partitions/manifest-layout-preview` (`manifest=null`) | `unavailable`, `write_allowed=false` |
| UI `http://127.0.0.1:3001/` | **HTTP 200** |
| Offizielles JS-Bundle (Deploy) | **`index-B-1eLB5j.js`** (aus `/opt/setuphelfer/frontend/dist/index.html`) |
| Bundle-Strings | `Sicherheitsvorschau`, `hardstop-preview` **vorhanden** |
| Quelle `PartitionSafetyPreviewPanel.tsx` unter `/opt` | **ja** |

### Browser-Smoke (Checkliste)

URL: `http://127.0.0.1:3001/?page=partitions`

- [ ] Seite „Partitionen“ öffnet
- [ ] Partition anklicken → Panel **„Sicherheitsvorschau“** unter Disk-Ansicht
- [ ] Hardstop-, Manifest-, Restore-Handoff-Bereiche sichtbar
- [ ] Keine Format-/Löschen-/Apply-Buttons im Phase-2-Panel
- [ ] Schreibschutz sichtbar (`write_allowed=false` / Schreibzugriff blockiert)

**Automatisiert bestätigt:** API + dist-Bundle + Gate. **Manuell:** Operator prüft Checkliste im Browser.

### Schreibschutz (unverändert)

- Keine Partitionierungs-, Format-, Lösch- oder Queue-Apply-Aktion ausgeführt.
- Kein Backup/Restore/Verify Deep in diesem Lauf.
- Queue/apply bleibt Phase-2-Stub.

### Abnahmeentscheidung

**Grün (Runtime formal):** offizieller Deploy, Gate Exit 0, API-Smoke read-only OK, UI-Bundle aus Deploy aktiv.

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
