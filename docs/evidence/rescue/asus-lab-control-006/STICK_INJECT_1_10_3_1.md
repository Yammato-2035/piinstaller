# Stick Inject 1.10.3.1

- Device: Ultra Line USB (by-label SETUPHELFER + SETUP_LOGS), serial hash not committed in Klartext
- Method: `inject-gui-bvr-fixes-into-stick-squashfs.sh --execute`
- Squashfs SHA256: `56a37200d7c3c72ead3f9fd8584a57fa36b4e578013b64e6a8d38d3d76491026`
- ESP carriers synced to `1.10.3.1`
- SETUP_LOGS WIN_DIAG includes live-capture + setup wrapper
- Host backup: `/tmp/filesystem.squashfs.lab006.pre-1.10.3.1.bak` (+ inject stamp backup)
- Residual: plain `opt/setuphelfer-rescue/rescue_payload_version` inside squashfs may lag until next inject (JSON authoritative)
