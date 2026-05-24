# Setuphelfer Rescue Live — Controlled Build Tree

- Source HEAD: 0d211fc
- Bundle MANIFEST sha256: 957191d080eed85e9dc082e673a6632837a6cca5305fafd20cf66f3424e5d257
- **real_iso_build_allowed:** false
- **usb_write_allowed:** false

## Vorbereitung (bereits erledigt durch prepare-controlled-live-build-tree.sh)

1. Temp-Runtime-Bundle unter `config/includes.chroot/opt/setuphelfer-rescue/`
2. Paketliste, systemd-networkd, local-only Services, Hooks

## ISO-Build (NUR nach Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
# NICHT automatisch:
# lb build
```

Siehe `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`.
