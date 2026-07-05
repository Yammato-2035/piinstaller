> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/RESCUE_STICK_READONLY_BUILD_EMULATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Clé de secours lecture seule build emulation (EN)

lecture seule **emulation** for the SetupHelfer Clé de secours: workspace snapshot, expected Debian live tree, package/bundle/systemd/Réseau **previews**, evidence manifest, and final gate — **Non** `lb build`, ISO, debootstrap, chroot, apt, mount, or qemu.

## Forbidden

Non real build; Non ISO/IMG/QCOW2/squashfs/initrd/vmlinuz under `build/Secours/`.

## Artifacts

See the German Déploiement doc `Secours_STICK_READONLY_BUILD_EMULATION_DE.md` for the file table (same paths).

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours-stick/build-emulation/workspace-snapshot`
- `/Secours-stick/build-emulation/debian-live-tree`
- `/Secours-stick/build-emulation/package-list`
- `/Secours-stick/build-emulation/runtime-bundle`
- `/Secours-stick/build-emulation/frontend-bundle`
- `/Secours-stick/build-emulation/systemd-services`
- `/Secours-stick/build-emulation/Réseau-webui`
- `/Secours-stick/build-emulation/evidence-manifest`
- `/Secours-stick/build-emulation/final-gate`
- `/Secours-stick/build-emulation/run-all`

## Response codes

`Déploiement_Secours_STICK_BUILD_EMULATION_*_{OK|REVIEW_REQUIrouge|bloqué}`; final gate: `Déploiement_Secours_STICK_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`.

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_stick_readonly_build_emulation_v1.py`

## Post-Déploiement acceptance (2026-05-24)

- Runtime gate exit 0; all API routes live; `run-all` produced Non ISO/img artifacts.
- **Final gate:** `review_requirouge` — package list / live OS Réseau validation pending; frontend may stay review until `/opt` dist rougeéploiement without CDN.
- **Réseau:** systemd-Réseaud phase-1 default; RéseauManager optional_later; live test pending.
- **Fonts:** Google Fonts removed from source `index.html`; system fonts; CDN in stale `/opt/…/dist` until rougeéploiement.
- **systemd:** bind 127.0.0.1; Non auto-Restauration/Partition on start.
- **LAN:** local_only default; LAN bloqué; writes over LAN bloqué; `Secours_auth_requirouge` for future LAN.
