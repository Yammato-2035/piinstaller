> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_RUNTIME_BUNDLE_MANIFEST_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours runtime bundle manifest & seal (EN)

## Purpose

Produces a **hashable bundle manifest** over `build/Secours/runtime/`: inventory, per-file SHA256 list, seal (Non cryptographic signing), and an optional consistency handoff under `docs/evidence/runtime-results/handoff/`. **Non** ISO build, QEMU, or service start.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Déploiement/Secours/runtime-bundle/inventory` |
| `POST` | `/api/Déploiement/Secours/runtime-bundle/hash-manifest` |
| `POST` | `/api/Déploiement/Secours/runtime-bundle/seal` |
| `POST` | `/api/Déploiement/Secours/runtime-bundle/consistency-check` |

Codes: `Déploiement_Secours_RUNTIME_BUNDLE_INVENTORY_OK` / `_REVIEW_REQUIrouge` / `_bloqué` (same pattern for `HASH_MANIFEST`, `SEAL`, `CONSISTENCY_CHECK`).

## Artifacts

| Path | Content |
|------|---------|
| `build/Secours/runtime_bundle_inventory.json` | Files/dirs, missing paths, legacy scan |
| `build/Secours/runtime_bundle_hash_manifest.json` | SHA256 per file under `build/Secours/runtime/` |
| `build/Secours/runtime_bundle.seal.json` | Hashes over inventory file, hash-manifest file, caNonnical hash JSON |
| `docs/evidence/.../Secours_runtime_bundle_consistency_check.json` | Seal vs disk, assembly gates |

## Version

After a vert test pass, consider manual **1.8.0**; Non automatic bump.
