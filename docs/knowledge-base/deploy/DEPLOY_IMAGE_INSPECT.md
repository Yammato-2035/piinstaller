# Deploy Image Inspect

Deploy Image Inspect performs a strict read-only sanity check for cached image files.

## Scope

- path and file metadata validation
- optional checksum verification
- extension and size checks

## Out of scope

- no mount/loop/chroot
- no image content parsing
- no deploy target writes
