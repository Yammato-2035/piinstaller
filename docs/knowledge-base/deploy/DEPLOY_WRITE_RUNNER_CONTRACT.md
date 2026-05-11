# KB: DEPLOY_WRITE_RUNNER_CONTRACT

## Überblick

Strukturierter **Deploy-Write-Job** für einen zukünftigen **privilegierten One-Shot-Runner**. Backend bleibt unprivilegiert; der Runner validiert nur **lokale** JSON-Jobs. **Aktuelle Phase:** Dry-Run ohne Device-Zugriff.

## Job-Schema (`schema_version` 1)

Pflichtfelder siehe `build_real_write_job` / `validate_real_write_job` in `backend/deploy/real_write_runner_contract.py`.

- `job_hash` = SHA256(kanonisches JSON aller Felder **außer** `job_hash`)
- `guard.hardware_gate_readiness` muss exakt `test_ready` sein
- `constraints.max_image_size_bytes` muss **536870912** (512 MiB) sein
- `max_bytes`: **> 0** und **≤ image_size_bytes**
- `target_device`: nicht-leer, Pfad unter `/dev/`

## Erlaubte Jobdatei-Pfade (`--job`)

- `/var/lib/setuphelfer/deploy-jobs/` und `backend/cache/deploy` (modulstabil); keine Symlinks auf der Jobdatei.

## Erlaubte Image-Pfade

- Gleiche Regel wie Image-Inspect-Cache **oder** Verzeichnis `backend/cache/deploy` (Modulpfad).

## CLI

`backend/tools/deploy_write_runner.py --job <file> --dry-run` → JSON auf stdout.

## Tests

- `backend/tests/test_deploy_write_runner_contract_v1.py`
- `backend/tests/test_deploy_write_runner_runtime_v1.py` (Containment, Symlink, Replay, CLI)

## Verwandt

- `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md`
- `docs/deploy/DEPLOY_REAL_WRITE_PROTOTYPE_DE.md` (Prototype-Write-API)
