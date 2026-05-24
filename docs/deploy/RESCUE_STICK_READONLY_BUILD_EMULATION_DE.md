# Deploy — Rettungsstick Read-only Build-Emulation (DE)

Read-only **Emulation** des Setuphelfer-Rettungssticks: Workspace-Snapshot, erwarteter Debian-Live-Baum, Paketlisten-/Bundle-/systemd-/Netzwerk-**Preview**, Evidence-Manifest und Final-Gate — **ohne** `lb build`, ISO, debootstrap, chroot, apt, mount oder qemu.

## Verbote

Kein echter Build, keine ISO/IMG/QCOW2/squashfs/initrd/vmlinuz unter `build/rescue/`.

## Artefakte

| Datei | Rolle |
|-------|--------|
| `build/rescue/emulation/rescue_stick_build_workspace_snapshot.json` | Repo/HEAD, Gate-Inputs |
| `build/rescue/emulation/rescue_stick_expected_debian_live_tree.json` | Erwartete lb-Struktur (`generated: false`) |
| `build/rescue/emulation/rescue_stick_package_list_preview.json` | Paketlisten-Vorschau |
| `build/rescue/emulation/rescue_stick_runtime_bundle_preview.json` | `/opt/setuphelfer`-Bundle |
| `build/rescue/emulation/rescue_stick_frontend_bundle_preview.json` | `frontend/dist` |
| `build/rescue/emulation/rescue_stick_systemd_service_preview.json` | Units |
| `build/rescue/emulation/rescue_stick_network_webui_preview.json` | localhost/LAN-Policy |
| `docs/evidence/.../rescue_stick_readonly_build_emulation_manifest.json` | SHA256 + Scans |
| `docs/evidence/.../rescue_stick_readonly_build_final_gate.json` | Final-Gate |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue-stick/build-emulation/workspace-snapshot`
- `/rescue-stick/build-emulation/debian-live-tree`
- `/rescue-stick/build-emulation/package-list`
- `/rescue-stick/build-emulation/runtime-bundle`
- `/rescue-stick/build-emulation/frontend-bundle`
- `/rescue-stick/build-emulation/systemd-services`
- `/rescue-stick/build-emulation/network-webui`
- `/rescue-stick/build-emulation/evidence-manifest`
- `/rescue-stick/build-emulation/final-gate`
- `/rescue-stick/build-emulation/run-all`

## Response-Codes

`DEPLOY_RESCUE_STICK_BUILD_EMULATION_*_{OK|REVIEW_REQUIRED|BLOCKED}`; Final-Gate: `DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_stick_readonly_build_emulation_v1.py`

## FAQ (Kurz)

**Warum noch kein ISO?** Erst alle Previews und Gates grün, dann separater Build-Auftrag.

**Warum `generated: false`?** Emulation beschreibt nur Erwartung, erzeugt keine echten Live-Artefakte.

**Warum kein apt/chroot/lb?** Verhindert versehentliche Host-/Stick-Writes und nicht reproduzierbare Halb-Builds.

**Warum Bundle-/Service-Preview zuerst?** Secrets, Branding, systemd-Sandbox und Netzwerkpolicy müssen vor dem Stick feststehen.

**Warum LAN gefährlich?** Offener Schreibzugriff ohne Gates im Rettungsmodus ist blockiert (`lan_write_without_gate: blocked`).

## Post-Deploy-Abnahme (2026-05-24)

- Runtime-Gate Exit 0; alle API-Routen sichtbar; `run-all` ohne echte Build-Artefakte.
- **Final-Gate:** `review_required` — Restpunkt Paketliste/Live-OS-Netzwerk; ggf. Frontend bis dist-Redeploy.
- **Netzwerk:** systemd-networkd Phase-1-Default; NetworkManager optional_later; Live-Test pending.
- **Fonts:** Keine Google-Fonts-Pflicht im Quell-`index.html`; Systemfonts; CDN in altem `/opt/…/dist` bis Redeploy.
- **systemd:** 127.0.0.1 für Backend und UI; kein Auto-Restore/Partition.
- **LAN:** `local_only`, LAN blockiert, Schreiben über LAN blockiert, später `rescue_auth_required`.
