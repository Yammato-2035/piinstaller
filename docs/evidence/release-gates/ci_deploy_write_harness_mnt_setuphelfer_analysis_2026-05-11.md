# CI — Deploy Write Harness `/mnt/setuphelfer` (setUp)

**Analysedatum:** 2026-05-12  
**Test:** `tests/test_deploy_write_harness_v1.py::TestDeployWriteHarnessV1::test_execute_writes_limited_and_sha`  
**Symptom (GitHub Actions):** `PermissionError: [Errno 13] Permission denied: '/mnt/setuphelfer'` beim `Path.mkdir(parents=True)` in `setUp` für `…/cache/deploy`.

## Phase 1 — Lokale Reproduktion

- **Befehl:** `cd backend && PYTHONPATH=. <venv>/python -m pytest tests/test_deploy_write_harness_v1.py::TestDeployWriteHarnessV1::test_execute_writes_limited_and_sha -vv`
- **Typisch lokal:** Oft **nicht** reproduzierbar, wenn `/mnt/setuphelfer` beschreibbar oder bereits existiert.
- **Stacktrace (CI):** `pathlib.Path.mkdir` → `os.mkdir` → `PermissionError` auf `/mnt/setuphelfer` beim rekursiven Anlegen von `/mnt/setuphelfer/cache/deploy`.
- **Beteiligung:** ausschließlich **Test-`setUp`** (`self.cache.mkdir`); kein Produktcode erzeugt diesen Pfad im Testlauf.

## Phase 2 — Testabsicht und Pfadstrategie

- **Fachlich:** Write-Harness prüft Session-Erstellung, Token, Limits, **begrenztes Lesen/Schreiben** (Bytes + SHA256), Single-Use, sowie Pfad- und Cache-Policies — alles auf **isolierten** Testzielen (`test_target_path` unter `/tmp/setuphelfer-deploy-test` bzw. `/mnt/setuphelfer/test-targets`).
- **Alt:** Quell-Image unter **`/mnt/setuphelfer/cache/deploy`** — entspricht einem produktiven Cache-Prefix, ist auf CI-Runnern aber **nicht beschreibbar**.
- **Gewünscht portabel:** Cache-Image unter einem Prefix aus `deploy.cache_execute._ALLOWED_CACHE_PREFIXES`, der im **Workspace** liegt: **`backend/cache/deploy`** (`_BACKEND_CACHE_DEPLOY`), weiterhin mit denselben Harness-Prüfungen (`_is_allowed_cached_image`, `_is_regular_safe_file_or_new`).

## Phase 3 — Produktcode

- `deploy/write_harness.py`: nutzt `_ALLOWED_CACHE_PREFIXES` aus `deploy/cache_execute.py` (u. a. `/mnt/setuphelfer/cache/deploy`, `_BACKEND_CACHE_DEPLOY`, …).
- **Produktiv** bleibt `/mnt/setuphelfer/cache/deploy` ein erlaubter Root — **unverändert**.
- **Test** nutzt nun denselben Mechanismus wie echte Deploy-Caches im Repo-Arbeitsbaum, ohne `/mnt` zu beschreiben.

## Phase 4 — Ursachenklasse

**A** — Der Test nutzte einen **echten** `/mnt/setuphelfer/…`-Pfad statt eines im Workspace beschreibbaren erlaubten Cache-Roots.

## Phase 5 — Minimaler Fix

- `setUp`: `self.cache = (_BACKEND / "cache" / "deploy").resolve()` + `mkdir`; Kommentar für CI.
- `tearDown`: `harness-src.img` entfernen (keine hinterlassenen Test-Artefakte im Cache-Verzeichnis).

Keine Änderung an `write_harness.py`-Sicherheitslogik, kein `sudo`, kein `mkdir` unter `/mnt` im Test.

## Phase 6 — Tests (lokal)

- `tests/test_deploy_write_harness_v1.py` — alle Methoden **grün**.
- `tests/test_deploy_*` — **grün**.
- `pytest tests/` — **1526 passed**.

## Phase 7 — CI-Folge

Nach `git push origin main`: `gh run list -R Yammato-2035/piinstaller --workflow ci.yml --limit 5` — **„CI grün“** nur bei GitHub **`conclusion: success`**; `ci_evidence.json` entsprechend nachziehen.
