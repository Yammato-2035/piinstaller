# CI-Analyse: Rescue-Dryrun `smartctl` fehlt (`test_2_target_capacity_red`)

**Datum:** 2026-05-11  
**Fehler (GitHub Actions):** `FileNotFoundError: smartctl` bei
`tests/test_rescue_restore_dryrun.py::TestRescueRestoreDryrun::test_2_target_capacity_red`.

## 1. Reproduktion / Kontext

`test_2_target_capacity_red` prüft im Dryrun, dass ein Zielgerät aufgrund unzureichender Kapazität zu `restore_risk_level == "red"` führt.
Der Test mockt dabei **nur** `modules.rescue_restore_dryrun.compare_backup_to_target` (Capacity-Ok/Result Codes).

Der Rest der Pipeline läuft weiterhin durch, inklusive `assess_target_device()` →
`smart_classify_disk()` →
`smart_classify_disk()` ruft `inspect_storage._run_capture(["smartctl", "-H", ...])` auf.

## 2. Produktcodepfad

**Datei:** `backend/modules/inspect_storage.py`

- `_run_capture()` verwendet `subprocess.run(argv, ...)`.
- Bei fehlendem Executable wirft `subprocess.run` **vor** der Rückgabe typischerweise `FileNotFoundError`.
- Vor der Fix-Änderung wurde dieser Fehler nicht abgefangen, sodass der Dryrun-Test im CI-Runner abbricht.

## 3. Ursachenklassifikation

**B)** Produktcode behandelt fehlendes `smartctl` nicht tolerant genug.

## 4. Minimaler Fix

**Änderung:** `backend/modules/inspect_storage.py`

- `_run_capture()` fängt `FileNotFoundError` ab und liefert ein Dummy-`CompletedProcess`:
  - `returncode = 127`
  - `stdout = ""`
  - `stderr = <Fehlertext>`

Dadurch kann `smart_classify_disk()` den Text prüfen und auf `risk_code = "rescue.smart.not_available"` / Fallback umstellen,
ohne den Prozess mit einer Exception zu stoppen.

## 5. Ausgeführte Tests (lokal)

- `tests/test_rescue_restore_dryrun.py` (5 Tests) — **passed**
- `tests/test_rescue* tests/*storage* tests/test_safe_device*` — **58 passed**
- Vollsuite `tests/` — **1526 passed**

## 6. Evidence-Status

CI bleibt bis zum nächsten Workflow-Lauf **rot**, bis GitHub Actions wieder erfolgreich durchläuft.

