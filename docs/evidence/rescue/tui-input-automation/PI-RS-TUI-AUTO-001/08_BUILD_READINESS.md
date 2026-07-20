# 08 Build Readiness

## STOP — no payload/USB in this phase

Proposed next controlled order (needs explicit operator approval):

1. Payload bump already at **1.10.0.59** in workspace SoT
2. Repack or inject squashfs including new CLI/unit + GRUB patch on ESP
3. Verify carriers: VERSION, rescue_payload_version.json, version.json, squash SHA, grub SHA
4. Dual confirmation before USB write
5. MSI boot of diagnostic GRUB entry only

Rollback: previous squash host backup from inject script; prior GRUB `.prev-*` files on ESP.
