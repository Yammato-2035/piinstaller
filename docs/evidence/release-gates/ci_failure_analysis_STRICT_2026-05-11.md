# STRICT – CI-Failure-Analyse (`ci.yml`)

**Analysiert:** 2026-05-11  
**Run:** `25628733872` · **Workflow:** CI · **Repo:** `Yammato-2035/piinstaller`

## 1. Geprüfter CI-Run

| Feld | Wert |
|------|------|
| run_id (databaseId) | 25628733872 |
| conclusion | failure |
| branch | main |
| commit (headSha) | `671fe625170e7681762caa19699823d8bcd905d0` |
| started_at (Run) | 2026-05-10T12:28:29Z |
| workflow | `.github/workflows/ci.yml` |
| URL | https://github.com/Yammato-2035/piinstaller/actions/runs/25628733872 |

## 2. Fehlschlagender Job

- **Job-Name:** `lint-and-test`  
- **job_id (databaseId):** `75228430020`  
- **URL:** https://github.com/Yammato-2035/piinstaller/actions/runs/25628733872/job/75228430020  

## 3. Fehlschlagender Step

- **Step:** `Pytest` (Step 8)  
- **Ruff / Bandit:** `success` (`continue-on-error: true` in Workflow für Ruff/Bandit)  
- **Pytest-Befehl (CI):** `python -m pytest tests/ -v --tb=short -x` (working-directory: `backend`)

## 4. Genaue Ursache

Logauszug (Job-Logs per `gh api …/jobs/75228430020/logs`):

```text
ERROR collecting tests/test_deploy_runner_rescue_build_environment_emulation_v1.py
ModuleNotFoundError: No module named 'deploy.runner_rescue_io'
```

- Beim **Collect** von `test_deploy_runner_rescue_build_environment_emulation_v1.py` wird `deploy.runner_rescue_build_environment_emulation` geladen; dieses Modul importiert `deploy.runner_rescue_io` (`from deploy.runner_rescue_io import …`).
- **GitHub-Tree** zu Commit `671fe625…`: Unter `backend/deploy/` existieren nur **drei** Dateien: `routes.py`, `runner_rescue_build_environment_emulation.py`, `runner_rescue_sandbox_controlled_copy.py`. **`runner_rescue_io.py` fehlt im Remote-Repository.**
- **Lokal:** Vollständiger `backend/deploy/`-Baum auf der Platte (viele Module); `pytest` kann importieren → daher Diskrepanz **Remote vs. lokaler Arbeitskopie** (nicht primär Python-/OS-Unterschied).

## 5. Lokaler Unterschied

- CI: frischer Clone = nur das, was auf `main` committed ist → fehlender Submodul-/Package-Teil `runner_rescue_io` → sofortiger Collect-Error.  
- Lokal: Datei `backend/deploy/runner_rescue_io.py` vorhanden (in typischer Arbeitskopie ggf. **untracked** `??` relativ zu Git) → Collection gelingt, volle Suite kann laufen.

## 6. Empfohlener minimaler Fix (nur Vorschlag, keine Produktlogik-Änderung)

1. **`backend/deploy/runner_rescue_io.py`** auf `main` **committen und pushen** (reine Vervollständigung des bereits referenzierten Pakets; Datei ist stdlib-only, keine Secrets).  
2. CI erneut laufen lassen: `pytest -x` stoppt beim **ersten** Fehler — es können **weitere** fehlende `deploy.*`-Module folgen, solange Remote-`backend/deploy/` nicht vollständig mit dem intendierten Stand übereinstimmt. Dann fehlende Imports analog ergänzen oder Remote-Baum bewusst mit Workspace abgleichen (Release-/Repo-Hygiene, kein Feature).

## 7. Geänderte Evidence-Dateien (diese Analyse)

- `docs/evidence/release-gates/ci_evidence.json`  
- `docs/evidence/release-gates/ci_failure_analysis_STRICT_2026-05-11.md` (dieses Dokument)  
- `docs/evidence/release-gates/release_readiness_gate.json`  
- `docs/evidence/release-gates/release_readiness_report.md`  
- `docs/roadmap/STATUS_MATRIX.md`  
- `docs/evidence/release-gates/blocker_inventory.json`  

## 8. CI weiterhin rot?

**Ja**, solange kein neuer grüner Lauf auf `main` existiert und der fehlende Import nicht im Repository behoben ist.

---

*Tippfehler `ci_eidence.json`: im Repo nicht vorhanden; korrekter Name bleibt `ci_evidence.json`.*
