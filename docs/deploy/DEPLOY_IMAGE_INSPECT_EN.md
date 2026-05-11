# Deploy Image Inspect (EN)

## Goal

Read-only pre-check of a locally cached image before future deploy approval.

## Allowed checks

- file exists
- regular file
- path under allowed Setuphelfer cache
- extension (.img/.iso/.qcow2)
- file size > 0
- optional SHA256 verification when expected_checksum is provided

## Not allowed

- no mount/loop-device
- no extract
- no partition analysis
- no image content inspection
- no installation
