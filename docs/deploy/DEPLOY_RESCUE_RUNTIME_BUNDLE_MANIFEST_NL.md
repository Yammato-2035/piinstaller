> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_RUNTIME_BUNDLE_MANIFEST_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding runtime bundle manifest & seal (EN)

## Purpose

Produces a **hashable bundle manifest** over `build/roodding/runtime/`: inventory, per-file SHA256 list, seal (Nee cryptographic signing), and an optional consistency handoff under `docs/evidence/runtime-results/handoff/`. **Nee** ISO build, QEMU, or service start.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Deploy/roodding/runtime-bundle/inventory` |
| `POST` | `/api/Deploy/roodding/runtime-bundle/hash-manifest` |
| `POST` | `/api/Deploy/roodding/runtime-bundle/seal` |
| `POST` | `/api/Deploy/roodding/runtime-bundle/consistency-check` |

Codes: `Deploy_roodding_RUNTIME_BUNDLE_INVENTORY_OK` / `_REVIEW_REQUIrood` / `_geblokkeerd` (same pattern for `HASH_MANIFEST`, `SEAL`, `CONSISTENCY_CHECK`).

## Artifacts

| Path | Content |
|------|---------|
| `build/roodding/runtime_bundle_inventory.json` | Files/dirs, missing paths, legacy scan |
| `build/roodding/runtime_bundle_hash_manifest.json` | SHA256 per file under `build/roodding/runtime/` |
| `build/roodding/runtime_bundle.seal.json` | Hashes over inventory file, hash-manifest file, caNeenical hash JSON |
| `docs/evidence/.../roodding_runtime_bundle_consistency_check.json` | Seal vs disk, assembly gates |

## Version

After a groen test pass, consider manual **1.8.0**; Nee automatic bump.
