# Deploy — Rescue runtime bundle manifest & seal (EN)

## Purpose

Produces a **hashable bundle manifest** over `build/rescue/runtime/`: inventory, per-file SHA256 list, seal (no cryptographic signing), and an optional consistency handoff under `docs/evidence/runtime-results/handoff/`. **No** ISO build, QEMU, or service start.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/deploy/rescue/runtime-bundle/inventory` |
| `POST` | `/api/deploy/rescue/runtime-bundle/hash-manifest` |
| `POST` | `/api/deploy/rescue/runtime-bundle/seal` |
| `POST` | `/api/deploy/rescue/runtime-bundle/consistency-check` |

Codes: `DEPLOY_RESCUE_RUNTIME_BUNDLE_INVENTORY_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (same pattern for `HASH_MANIFEST`, `SEAL`, `CONSISTENCY_CHECK`).

## Artifacts

| Path | Content |
|------|---------|
| `build/rescue/runtime_bundle_inventory.json` | Files/dirs, missing paths, legacy scan |
| `build/rescue/runtime_bundle_hash_manifest.json` | SHA256 per file under `build/rescue/runtime/` |
| `build/rescue/runtime_bundle.seal.json` | Hashes over inventory file, hash-manifest file, canonical hash JSON |
| `docs/evidence/.../rescue_runtime_bundle_consistency_check.json` | Seal vs disk, assembly gates |

## Version

After a green test pass, consider manual **1.8.0**; no automatic bump.
