# Worktree-Hygiene nach Partitionshelfer Phase 1

**Datum:** 2026-05-23  
**HEAD (Start):** `cce81de`  
**Auftrag:** Artefakt-Cleanup, Secret-Tracking, keine fachfremden Commits

---

## Runtime (lesend)

| Prüfung | Ergebnis |
|---------|----------|
| `check-runtime-deploy-gate.sh` | **Exit 0** |
| `GET /openapi.json` | **200** |
| Partition-Pfade in OpenAPI | `/api/partitions/scan`, `safety-check`, `queue`, `queue/{action_id}`, `queue/apply` |
| `GET /api/partitions/scan` | **200** |

---

## Secret-Tracking

| Pfad | Getrackt? | Lokal vorhanden? | `.gitignore` |
|------|-----------|------------------|--------------|
| `.env` | **nein** | ja | Zeile `.env` |
| `.sudo_key` | **nein** | ja | Zeile `.sudo_key` |
| `.venv/` | **nein** | — | ja |
| `.pytest_cache/` | **nein** | — | ergänzt |
| `scripts/__pycache__/` | **nein** | entfernt (untracked) | `__pycache__/` |

**STOP-Kriterium nicht ausgelöst** — keine Secrets im Index.

---

## `tmp_runner_img.img`

| Eigenschaft | Wert |
|-------------|------|
| Größe | 1 Byte (Platzhalter) |
| Verwendung | `backend/tests/test_deploy_write_runner_contract_v1.py` erzeugt die Datei in `test_image_path_outside_cache_invalid` selbst (`write_bytes`) |
| Historie | Commit `36d234b` (Workspace-Sync) |
| Entscheidung | **Aus Git-Index entfernt** — generiertes Runner-Test-Artefakt, kein Fixture |

Lokal bleibt die Datei erhalten; Tests schreiben bei Bedarf neu.

---

## Weitere getrackte Deploy-`*.img` (bereinigt)

Aus Index entfernt (lokal unter `cache/deploy/` weiter möglich):

- `cache/deploy/big.img`, `ff.img`, `fp.img`, `h.img`, `m.img`, `nf.img`, `ok.img`, `ro.img`, `vm.img`

`backend/cache/deploy/` war bereits in `.gitignore`; Root-`cache/deploy/` fehlte.

---

## `.gitignore` Änderungen

Ergänzt:

- `cache/deploy/`
- `tmp_runner_img.img`
- `*.img`, `*.img.tmp`, `*.qcow2`, `*.iso`
- `.pytest_cache/`
- `.npm-cache/`

**Ausnahmen:** Keine versionierten `*.img`/`*.iso`-Fixtures im Repo (Stand: `git ls-files` leer nach Cleanup).

---

## Untracked Dateien (Klassifikation)

| Klasse | Pfade | Entscheidung |
|--------|-------|--------------|
| **A Cursor-Regeln** | `.cursor/rules/*.md`, `*.mdc` (18 Dateien) | **Nicht committen** — keine Freigabe im Auftrag |
| **B Cache** | `.npm-cache/` | **Ignorieren** — lokal entfernt, `.gitignore` ergänzt |
| **C Evidence** | `docs/evidence/runtime-results/BR-001-full-root-or-profile-2026-05-17.json` | **Später prüfen** — nicht verifiziert |
| **C Snapshot** | `frontend/public/dev-dashboard.snapshot.json` | **Nicht committen** — generiert |
| **D Packaging** | `packaging/systemd/setuphelfer-backup@.service.d/backup-target.conf.example` | **Später prüfen** — separates Thema |

---

## Modified Dateien (Klassifikation)

| Datei | Änderungstyp | Cleanup? | Risiko | Entscheidung |
|-------|--------------|----------|--------|--------------|
| `ckb-next` (Submodul) | dirty, 0 Zeilen Diff | nein | Submodule-Rauschen | **Nicht anfassen** |
| `LAB_ACCEPTANCE_REPORT*.json/md` | `generated_at` Timestamp | nein | Lab-Lauf | **Nicht committen** |
| `legacy_identifier_inventory.json` | `generated_at` | nein | Generator | **Nicht committen** |
| `frontend/src/lib/sudoUserMessages.ts` | NoNewPrivileges-Toast | nein | Feature | **Nicht committen** |
| `frontend/src/pages/Documentation.tsx` | Versions-/Changelog-Text | nein | UI-Doku | **Nicht committen** |
| `frontend/src/pages/RaspberryPiConfig.tsx` | `skip_test` sudo API | nein | Feature | **Nicht committen** |
| `packaging/helpers/setuphelfer-backup-starter.py` | `/media/setuphelfer` Root | nein | Host-spezifisch | **Nicht committen** |
| `setuphelfer-backend.dev-workspace.conf.example` | `ProtectHome` | nein | Systemd | **Nicht committen** |
| `notification-env.conf.example` | `ReadWritePaths`, 660-Hinweis | nein | Systemd | **Nicht committen** |

---

## Lokale Bereinigung (untracked only)

- `rm -rf .npm-cache/` — ausgeführt
- `rm -rf scripts/__pycache__/` — ausgeführt (war nicht getrackt)

---

## Tests

| Test | Ergebnis |
|------|----------|
| Runtime-Gate | OK |
| `py_compile` deploy/partitions/app | OK |
| `unittest test_partitions_api_v1` | ImportError `pytest` (Modul nutzt pytest; nicht installiert) |
| OpenAPI-Pfade (urllib) | 5 Partition-Pfade, `/scan` assert OK |

---

## Commit (Hygiene)

Geplant: `.gitignore`, Index-Entfernung `*.img`, diese Evidence-Datei.

**Nicht gestaged:** fachfremde Modified/Untracked aus Tabelle oben.

---

## Verbleibende Review-Punkte

1. Submodul `ckb-next` dirty — lokal bereinigen oder bewusst ignorieren.
2. Lab-/Runtime-Evidence-Timestamps — separater Lab-Commit oder verwerfen.
3. Frontend sudo/Documentation-Änderungen — eigenes Feature-PR.
4. `backup-target.conf.example` — Packaging-Review.
5. Vollständiger `sudo deploy-to-opt.sh` falls `/opt` und Workspace bei `deploy/routes.py` divergieren (Gate derzeit OK).
