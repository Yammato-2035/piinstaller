> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_IMAGE_INSPECT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Image Inspect (EN)

## Goal

alleen-lezen pre-check of a locally cached image before future Deploy approval.

## Allowed checks

- file exists
- regular file
- path under allowed Setuphelfer cache
- extension (.img/.iso/.qcow2)
- file size > 0
- optional SHA256 verification when expected_checksum is provided

## Neet allowed

- Nee mount/loop-Apparaat
- Nee extract
- Nee Partitie analysis
- Nee image content inspection
- Nee installation
