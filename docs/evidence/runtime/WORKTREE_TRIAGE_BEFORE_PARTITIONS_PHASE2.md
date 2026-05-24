# Worktree-Triage vor Partitionshelfer Phase 2

**Datum:** 2026-05-23  
**HEAD:** `f008945` (`main`)  
**Vorgänger-Hygiene:** `docs/evidence/runtime/WORKTREE_HYGIENE_AFTER_PARTITIONS.md`

---

## Runtime-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** |

Kein Deploy in diesem Auftrag.

---

## OpenAPI-Regression (Partitions)

```python
paths = [
  '/api/partitions/queue',
  '/api/partitions/queue/apply',
  '/api/partitions/queue/{action_id}',
  '/api/partitions/safety-check',
  '/api/partitions/scan',
]
assert '/api/partitions/scan' in paths  # OK
```

`GET /openapi.json` → **200**, keine Regression nach Hygiene-Commit.

---

## Offene Dateien – Klassifikation

| Datei | Gruppe | Änderungstyp | Risiko | Empfehlung |
|-------|--------|--------------|--------|------------|
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json` | 1 Lab-Evidence | `generated_at` Timestamp | niedrig | Separater Lab-Commit oder verwerfen |
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md` | 1 Lab-Evidence | `generated_at` | niedrig | wie JSON |
| `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md` | 1 Lab-Evidence | `generated_at` | niedrig | wie JSON |
| `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json` | 1 Lab-Evidence | `generated_at` | niedrig | Separater Generator-Lauf oder revert |
| `docs/evidence/runtime-results/BR-001-full-root-or-profile-2026-05-17.json` | 6 Snapshot | untracked Runtime-Evidence | mittel | Erst verifizieren, dann gezielt committen |
| `frontend/src/lib/sudoUserMessages.ts` | 2 Frontend/Doku | NoNewPrivileges-Toast | mittel | Separates Feature-PR (sudo/NNP) |
| `frontend/src/pages/Documentation.tsx` | 2 Frontend/Doku | Versions-/Changelog-Text | niedrig | Mit Frontend-PR oder revert |
| `frontend/src/pages/RaspberryPiConfig.tsx` | 2 Frontend/Doku | `skip_test` sudo API | mittel | Separates Feature-PR |
| `frontend/public/dev-dashboard.snapshot.json` | 6 Snapshot | untracked, generiert | niedrig | **Nicht committen** (Snapshot) |
| `packaging/helpers/setuphelfer-backup-starter.py` | 3 Packaging/Systemd | `/media/setuphelfer` Allowlist | **hoch** (host-spezifisch) | Eigener Packaging-Commit mit Review |
| `packaging/systemd/setuphelfer-backend.dev-workspace.conf.example` | 3 Packaging/Systemd | `ProtectHome=read-only` | mittel | Eigener Systemd-PR |
| `packaging/systemd/setuphelfer-backend.service.d/notification-env.conf.example` | 3 Packaging/Systemd | `ReadWritePaths`, 660-Hinweise | mittel | Eigener Systemd-PR |
| `packaging/systemd/setuphelfer-backup@.service.d/backup-target.conf.example` | 3 Packaging/Systemd | untracked Example | niedrig | Separates Packaging-Review |
| `ckb-next` (Submodul) | 4 Submodule | `-dirty`, gleicher SHA | niedrig–mittel | **Nicht committen** (siehe unten) |
| `.cursor/rules/*.md` (16 Dateien) | 5 Cursor-Regeln | untracked Regeln | niedrig | Nur nach bewusster Freigabe |
| `.cursor/rules/*.mdc` (3 Dateien) | 5 Cursor-Regeln | untracked Regeln | niedrig | wie oben |

**Keine Datei aus dieser Tabelle in Phase-2-Vorbereitung stagen.**

---

## Submodul `ckb-next`

| Feld | Wert |
|------|------|
| `git submodule status` | `5fb355df… ckb-next (v0.2.9-1306-g5fb355df)` |
| Parent-Diff | `Subproject commit …7` → `…7-dirty` (kein SHA-Wechsel) |
| `git -C ckb-next status` | **blockiert** — `dubious ownership` (safe.directory fehlt für diesen User) |

**Entscheidung:** Submodul-Änderung **nicht bewusst** für Partitions Phase 2. Vermutlich lokale Modifikationen oder Dateimodi im Submodul-Tree. **Nicht committen.** Später: `safe.directory` setzen (Operator), `git -C ckb-next status`, ggf. `git submodule update --init` oder gezieltes Submodule-PR.

---

## Testumgebung

| Interpreter | pytest |
|-------------|--------|
| `/usr/bin/python3` (3.12.3) | **fehlt** |
| `./venv/bin/python3` | nicht vorhanden |
| `./.venv/bin/python3` | **fehlt** |
| `./backend/venv/bin/python3` | **pytest 9.0.3** |
| `./backend/.venv/bin/python3` | **pytest 9.0.3** |
| `/opt/setuphelfer/backend/venv/bin/python3` (Runtime) | **fehlt** |

**CI** (`.github/workflows/ci.yml`): `pip install pytest pytest-asyncio httpx`, dann `python -m pytest tests/` aus `backend/`.

**Empfehlung für lokale/Phase-2-Tests:**

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m pytest backend/tests/test_partitions_api_v1.py -q
```

Kein `apt install`, kein pip in Runtime-venv in diesem Auftrag.

---

## `test_partitions_api_v1.py` – Teststil-Befund

| Frage | Antwort |
|-------|---------|
| pytest-basiert? | **Ja** — `import pytest`, `@pytest.fixture def client()` |
| unittest-basiert? | **Nein** — nicht mit `unittest`/`TestCase` lauffähig |
| Umbenennen nötig? | **Nein** — `_v1.py`-Konvention passt zum Repo |
| Anpassung empfohlen? | **Ja (separater Fix):** `test_tkinter_fallback_still_present` nutzt falschen Pfad |

**Pfad-Bug (6/7 Tests grün, 1 rot):**

```python
root = Path(__file__).resolve().parents[2].parent / "apps" / "partitionshelfer"
# → /home/volker/apps/partitionshelfer (falsch)
# korrekt: parents[2] / "apps" / "partitionshelfer" → Repo-Root/piinstaller/apps/...
```

Lauf mit `backend/venv`:

```
6 passed, 1 failed (test_tkinter_fallback_still_present)
```

Für Phase-2 Safety Contracts: Testdatei **pytest-kompatibel belassen**; Pfad in eigenem Commit korrigieren; CI nutzt ohnehin pytest aus `backend/tests/`.

---

## Empfohlene separate Commits (Reihenfolge)

1. **fix(tests):** Pfad in `test_tkinter_fallback_still_present` (1 Zeile)
2. **feat(frontend):** sudo NNP + `skip_test` + Doku-Texte (3 Dateien, gemeinsam oder getrennt)
3. **chore(packaging):** backup-starter Allowlist + systemd-Examples (Review: host-spezifische Pfade)
4. **docs/evidence(lab):** Lab-Acceptance + legacy inventory (nur nach verifiziertem Generator-Lauf)
5. **chore(submodule):** ckb-next nur bei bewusster SHA-/Inhaltsänderung
6. **chore(cursor):** Regeln nur nach expliziter Freigabe

**Partitions Phase 2** startet erst, wenn Worktree für Phase-2-Dateien sauber ist oder Änderungen in obigen Commits isoliert sind.

---

## Schreibschutz

Unverändert: kein Partition-Write, kein Backup/Restore, keine Safety-Gates geschwächt.
