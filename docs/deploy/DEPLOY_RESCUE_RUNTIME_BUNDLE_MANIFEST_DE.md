# Deploy — Rescue Runtime Bundle Manifest & Seal (DE)

## Zweck

Erzeugt ein **hashbares Bundle-Manifest** über `build/rescue/runtime/`: Inventar, SHA256-Hashliste, Seal (ohne kryptografische Signatur) und optionaler Konsistenz-Handoff unter `docs/evidence/runtime-results/handoff/`. **Kein** ISO-Build, kein QEMU, kein Service-Start.

## API

| Methode | Pfad |
|---------|------|
| `POST` | `/api/deploy/rescue/runtime-bundle/inventory` |
| `POST` | `/api/deploy/rescue/runtime-bundle/hash-manifest` |
| `POST` | `/api/deploy/rescue/runtime-bundle/seal` |
| `POST` | `/api/deploy/rescue/runtime-bundle/consistency-check` |

Codes: `DEPLOY_RESCUE_RUNTIME_BUNDLE_INVENTORY_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (analog für `HASH_MANIFEST`, `SEAL`, `CONSISTENCY_CHECK`).

## Artefakte

| Pfad | Inhalt |
|------|--------|
| `build/rescue/runtime_bundle_inventory.json` | Dateien/Verzeichnisse, fehlende Pfade, Legacy-Scan |
| `build/rescue/runtime_bundle_hash_manifest.json` | SHA256 je Datei unter `build/rescue/runtime/` |
| `build/rescue/runtime_bundle.seal.json` | Hashes über Inventar-Datei, Hash-Manifest-Datei, kanonisches Hash-JSON |
| `docs/evidence/.../rescue_runtime_bundle_consistency_check.json` | Abgleich Seal vs. Platte, Gates |

## Version

Nach grüner Kette manuell **1.8.0** erwägen; kein automatischer Bump.
