# Deploy — Rescue Sandbox Controlled Copy (DE)

Strikt begrenzte **Ausführung** der vorbereiteten Sandbox-Kopierplaene: nur Dateien aus `sandbox_config_copy_plan.json` / `sandbox_runtime_copy_plan.json`, Ziele nur unter `build/rescue/sandbox/config-copy/` bzw. `runtime-copy/`, SHA256 fuer Quelle und Ziel, atomischer `.tmp`-Write, Verifikation, Seal und Final-Gate. **Kein** ISO-Build, kein live-build, kein debootstrap/Chroot, kein apt install, kein mount, keine VM, kein dd/mkfs, kein systemctl, kein Release/Publish.

## Artefakte

| Datei | Rolle |
|-------|--------|
| `docs/evidence/.../rescue_sandbox_copy_execution_precheck.json` | Precheck (Gates, Safety, Pfade, Groesse, Symlinks) |
| `build/rescue/sandbox/manifests/config_copy_result.json` | Ergebnis Config-Kopie inkl. Hashes |
| `build/rescue/sandbox/manifests/runtime_copy_result.json` | Ergebnis Runtime-Kopie inkl. Hashes |
| `docs/evidence/.../rescue_sandbox_copy_verify_result.json` | Hash-/Plan-/Zielbaum-Pruefung |
| `build/rescue/sandbox/manifests/sandbox_copy.seal.json` | SHA256 ueber Ergebnis-JSONs und Verify-Handoff (Rohbytes) |
| `docs/evidence/.../rescue_sandbox_copy_final_gate.json` | Aggregiert Precheck, Verify, Seal, Branding, Zero-State |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/sandbox-copy/precheck`
- `/rescue/sandbox-copy/config`
- `/rescue/sandbox-copy/runtime`
- `/rescue/sandbox-copy/verify`
- `/rescue/sandbox-copy/seal`
- `/rescue/sandbox-copy/final-gate`

Request-Body wie ueblich `explicit_overwrite` (bool) fuer Handoff-/Ergebnisdateien.

## Response-Codes

`DEPLOY_RESCUE_SANDBOX_COPY_PRECHECK_{OK|REVIEW_REQUIRED|BLOCKED}` und analog fuer `CONFIG`, `RUNTIME`, `VERIFY`, `SEAL`; Final-Gate: `DEPLOY_RESCUE_SANDBOX_COPY_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_sandbox_controlled_copy_v1.py`
