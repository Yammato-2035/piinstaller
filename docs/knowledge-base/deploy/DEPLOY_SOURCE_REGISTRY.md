# Deploy Source Registry

Deploy Source Registry is a metadata-only catalog of deploy sources used by preview/execute planning.

## What it does

- lists predefined sources and constraints
- validates local image entries by filesystem metadata only
- validates remote image metadata (no network calls)
- evaluates source compatibility against inspect + deploy plan context

## What it does NOT do

- no downloads
- no image imports
- no mount/chroot
- no installation
