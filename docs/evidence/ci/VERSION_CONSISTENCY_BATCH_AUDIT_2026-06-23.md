# Version Consistency Batch Audit

## Ausgangslage

- **CI-Fehler:** `test_backend_version_gate_v1.py::test_version_consistency_module_import` — `AssertionError: '1.9.5.2' != '1.7.3.1'`
- **CI-Run:** `28041403971` (rot, 104 Tests vor `-x`-Stop)
- **HEAD (vor Fix):** `42c94fe` (`fix(ci): update e6 router roadmap contract`)
- **Branch:** `main`
- **Security:** grün (`28041402935`)
- **Preflight staged (16 Dateien, unangetastet):** `.github/workflows/*`, `CHANGELOG.md`, `backend/core/rescue_build_manifest.py`, Rescue-Skripte, `docs/security/PREFLIGHT_AND_VERSION_GATES.md`, u. a.

## Gefundene Versionsquellen

| Quelle | Datei | Wert (vor Fix, committed) | Maßgeblich? | Bewertung |
|---|---|---|---|---|
| SSOT | `config/version.json` | `1.9.5.2` | **ja** | Canonical, aber hinter Frontend-Drift |
| Root | `VERSION` | `1.9.5.2` | abgeleitet | Sync aus SSOT |
| Root npm | `package.json` | `1.9.5.2` | abgeleitet | Sync aus SSOT |
| Frontend npm | `frontend/package.json` | `1.9.16.1` | abgeleitet | **Drift** gegen SSOT |
| Frontend lock | `frontend/package-lock.json` | `1.9.16.1` | abgeleitet | **Drift** gegen SSOT |
| Tauri | `frontend/src-tauri/tauri.conf.json` | `1.9.5` | abgeleitet | Semver-Projektion, hinter SSOT |
| Cargo | `frontend/src-tauri/Cargo.toml` | `1.9.5` | abgeleitet | Semver-Projektion |
| Tauri resource | `frontend/src-tauri/resources/setuphelfer-version.json` | `1.9.5.2` | abgeleitet | Hinter SSOT |
| deb changelog | `frontend/src-tauri/deb-changelog.txt` | `1.9.5.2` | abgeleitet | Hinter SSOT |
| Backend API | `backend/core/versioning.py` | liest SSOT | nein | korrekt |
| Consistency tool | `backend/tools/check_version_consistency.py` | prüft SSOT | Gate | Exit 17 bei Drift |
| Gate-Test | `backend/tests/test_backend_version_gate_v1.py` | erwartete `1.7.3.1` | **falsch** | Veraltete Hardcodierung |
| Projection tests | `backend/tests/test_version_projection_v1.py` | Fixture `1.7.3.1` | nein | Bewusste Testdaten |
| Consistency tests | `backend/tests/test_version_consistency_v1.py` | Fixture `1.7.3.1` | nein | Temporäre Testbäume |
| Rescue evidence | `docs/evidence/rescue/*` | `1.9.5.2` | nein | Historisch, nicht geändert |
| DCC evidence | `docs/evidence/dev-dashboard/developer_dcc_usb_toolbox_visibility_latest.json` | `1.7.3.1` | nein | Runtime-Snapshot, historisch |

## Entscheidung

| Frage | Entscheidung | Begründung |
|---|---|---|
| Single Source of Truth? | `config/version.json` → `project_version` | Projektregel und `sync-version.js` |
| 1.9.5.2 oder 1.7.3.1 korrekt? | **Keines** — beide veraltet/inkonsistent | CI: SSOT `1.9.5.2`, Test hardcodiert `1.7.3.1` |
| Neuere Version `1.9.16.1`? | **Ja, Zielversion** | `frontend/package.json` bereits `1.9.16.1` auf `main`; CHANGELOG-Eintrag; lokale Konsistenz |
| CI-Test auf altem Stand? | **Ja** | Erwartung `1.7.3.1` statt SSOT-Lesen |
| Rollback auf 1.9.5.2? | **Nein** | Würde Frontend-Drift verschärfen |

## Durchgeführter Fix

1. **`config/version.json`** → `project_version: "1.9.16.1"`
2. **`cd frontend && node sync-version.js`** → `VERSION`, `package.json`, Tauri/Cargo/deb-changelog/resource
3. **`backend/tests/test_backend_version_gate_v1.py`** → erwartet `canonical` aus `config/version.json`, prüft `ok=True`

## Geänderte Dateien (Commit)

- `config/version.json`
- `VERSION`
- `package.json`
- `frontend/src-tauri/tauri.conf.json`
- `frontend/src-tauri/Cargo.toml`
- `frontend/src-tauri/deb-changelog.txt`
- `frontend/src-tauri/resources/setuphelfer-version.json`
- `backend/tests/test_backend_version_gate_v1.py`
- `docs/evidence/ci/VERSION_CONSISTENCY_BATCH_AUDIT_2026-06-23.md`

## Bewusst nicht geändert

- Preflight-Bundle (16 staged Dateien)
- Historische Rescue-Evidence (`1.9.5.2`, `1.7.3.1` Snapshots)
- Projection-/Consistency-Fixture-Tests mit `1.7.3.1` als Testdaten
- `docs/developer/VERSIONING.md` Beispieltexte (Dokumentation, kein Gate)
- `build/rescue/**` Artefakte

## Lokale Validierung

```
python3 backend/tools/check_version_consistency.py --repo-root .  → ok=True
pytest backend/tests/test_backend_version_gate_v1.py … (8 Module) → 38 passed
pip-audit -r backend/requirements.txt → No known vulnerabilities
npm audit --omit=dev --audit-level=high → 0 vulnerabilities
```

## Erwartetes CI-Ergebnis

- Version-Gate-Test grün (dynamischer Canonical-Check + konsistenter Workspace)
- Keine Regression in E4/E5/E6/E11/Fix9/Anti-Regression
- Security weiterhin grün

## Nach Fix (ausfüllen nach Push)

- **Commit:** (siehe `git log -1`)
- **CI-Run:** (siehe `gh run list`)
- **CI-Ergebnis:** (pending)
