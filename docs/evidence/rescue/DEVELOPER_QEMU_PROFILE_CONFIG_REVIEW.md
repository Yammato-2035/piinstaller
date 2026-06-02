# Developer QEMU Profile — Config Review (Phase 1)

**Datum:** 2026-06-02  
**Log:** `developer_qemu_profile_occurrences_latest.log`  
**Config-Dateien:** `developer_qemu_profile_config_files_latest.log` (21 Einträge unter `config/`)

## Fragen & Antworten

### Wo wird `LB_BOOTAPPEND_LIVE` gesetzt?

Nicht direkt als Env-Variable. `prepare-controlled-live-build-tree.sh` schreibt `auto/config` mit `--bootappend-live "…"` (live-build liest das als effektive Bootappend-Quelle).

### Wo wird `quiet splash` gesetzt?

- **Standard-Profil:** `auto/config` → `quiet splash init=/lib/systemd/systemd`
- **developer-qemu:** explizit **ohne** `quiet splash` (Prepare-Zweig Zeile ~471–475)

### Wo ist `init=/lib/systemd/systemd` gesetzt?

In allen Profilen in `auto/config` bootappend-live (Standard und developer-qemu).

### Wo können `console=ttyS0` und `console=tty0` ergänzt werden?

| Ort | Mechanismus |
|-----|-------------|
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | `LIVE_BOOTAPPEND` für `developer-qemu` |
| `build/rescue/profiles/developer-qemu/` | Overlay (ISOLINUX `SERIAL 0`, GRUB-Hook 095) |
| `auto/config` | Materialisiert durch Prepare |

Nach Prepare (developer-qemu):

```
bootappend-live "… init=/lib/systemd/systemd console=tty0 console=ttyS0,115200n8 …"
```

ISOLINUX: `SERIAL 0 115200` in `config/bootloaders/isolinux/isolinux.cfg`.

### Gibt es bereits ein Developer-/QEMU-Profil?

**Ja:** `build/rescue/profiles/developer-qemu/` mit Hook `090-enable-qemu-smoke-autopilot.hook.chroot`, Autopilot-Service, Serial-Boot-Markers.

Aktivierung: `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu ./scripts/rescue-live/prepare-controlled-live-build-tree.sh`

### Services im Squashfs: vorhanden oder enabled?

| Service | Im Profil-Overlay | Enabled via Hook |
|---------|-------------------|------------------|
| `setuphelfer-qemu-smoke-autopilot.service` | yes | Hook 090 (`systemctl enable`) |
| `setuphelfer-dev-agent.service` | developer-Profil only | **Nein** bei developer-qemu (Autopilot-Unit übernimmt Report) |

Wants-Symlinks entstehen erst im Chroot während `lb build` — nicht im Prepare-only Tree.

## Status

**review_required** → nach Prepare mit developer-qemu: **ok** (Config-Marker materialisiert; Validate blockiert noch durch stale root-owned `binary/` von vorherigem Standard-Build)
