# Deploy Cache Execute Local-only

Local-only cache execute introduces the first controlled cache write path for deploy assets.

## Guarantees

- accepts local_image only
- rejects remote download paths
- validates token/session/ttl/source hash
- enforces allowed cache path containment
- optional checksum verification before copy

## Out of scope

- no image mount/extract/import
- no deploy/install/partition actions
- no writes to deploy target disks
