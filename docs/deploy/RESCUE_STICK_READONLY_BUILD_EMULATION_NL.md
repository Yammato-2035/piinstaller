> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/RESCUE_STICK_READONLY_BUILD_EMULATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — rooddingsstick alleen-lezen build emulation (EN)

alleen-lezen **emulation** for the SetupHelfer rooddingsstick: workspace snapshot, expected Debian live tree, package/bundle/systemd/Netwerk **previews**, evidence manifest, and final gate — **Nee** `lb build`, ISO, debootstrap, chroot, apt, mount, or qemu.

## Forbidden

Nee real build; Nee ISO/IMG/QCOW2/squashfs/initrd/vmlinuz under `build/roodding/`.

## Artifacts

See the German Deploy doc `roodding_STICK_READONLY_BUILD_EMULATION_DE.md` for the file table (same paths).

## API (`POST`, prefix `/api/Deploy`)

- `/roodding-stick/build-emulation/workspace-snapshot`
- `/roodding-stick/build-emulation/debian-live-tree`
- `/roodding-stick/build-emulation/package-list`
- `/roodding-stick/build-emulation/runtime-bundle`
- `/roodding-stick/build-emulation/frontend-bundle`
- `/roodding-stick/build-emulation/systemd-services`
- `/roodding-stick/build-emulation/Netwerk-webui`
- `/roodding-stick/build-emulation/evidence-manifest`
- `/roodding-stick/build-emulation/final-gate`
- `/roodding-stick/build-emulation/run-all`

## Response codes

`Deploy_roodding_STICK_BUILD_EMULATION_*_{OK|REVIEW_REQUIrood|geblokkeerd}`; final gate: `Deploy_roodding_STICK_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`.

## Tests

`Terugend/tests/test_Deploy_runner_roodding_stick_readonly_build_emulation_v1.py`

## Post-Deploy acceptance (2026-05-24)

- Runtime gate exit 0; all API routes live; `run-all` produced Nee ISO/img artifacts.
- **Final gate:** `review_requirood` — package list / live OS Netwerk validation pending; frontend may stay review until `/opt` dist roodeploy without CDN.
- **Netwerk:** systemd-Netwerkd phase-1 default; NetwerkManager optional_later; live test pending.
- **Fonts:** Google Fonts removed from source `index.html`; system fonts; CDN in stale `/opt/…/dist` until roodeploy.
- **systemd:** bind 127.0.0.1; Nee auto-Herstel/Partitie on start.
- **LAN:** local_only default; LAN geblokkeerd; writes over LAN geblokkeerd; `roodding_auth_requirood` for future LAN.
