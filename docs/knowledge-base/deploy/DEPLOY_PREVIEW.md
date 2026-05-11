# Deploy Preview

Deploy Preview is a no-write simulation layer for deploy: it binds to a deploy session and produces simulated steps for later execution phases.

## Guarantees

- no installation
- no image write
- no partitioning/formatting
- no mounts/chroot
- no service/network mutation

## Safety model

Preview requires a valid deploy session + token and exact target/profile/plan match. If plan safety blockers exist, preview is rejected.

## Remote images

`remote_image` is not downloaded in this phase. Only URL/checksum structure is validated and warning code `DEPLOY_PREVIEW_REMOTE_DOWNLOAD_BLOCKED` may be returned.
