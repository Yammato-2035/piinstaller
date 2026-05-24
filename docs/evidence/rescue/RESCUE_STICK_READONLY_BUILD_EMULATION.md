# Rescue stick — read-only build emulation (evidence)

**Date:** 2026-05-24  
**Runner:** `backend/deploy/runner_rescue_stick_readonly_build_emulation.py`
**Deploy baseline:** `60e3f31` (Add rescue stick readonly build emulation)

## Scope

Emulation only — no ISO, no `lb build`, no debootstrap/chroot/apt/mount/qemu/dd.

## Post-deploy acceptance (2026-05-24)

| Check | Result |
|-------|--------|
| `./scripts/check-runtime-deploy-gate.sh` | Exit **0** (vor/nach) |
| `setuphelfer-backend.service` / `setuphelfer.service` | **active** |
| OpenAPI `/api/deploy/rescue-stick/build-emulation/*` | **10 Routen** in Runtime |
| `POST …/run-all` | **review_required** (sauber; kein ISO) |
| Verbotene Artefakte (`find` iso/img/qcow2/squashfs/initrd/vmlinuz) | **keine** |
| Unit + Partitions-Regression | **grün** |

### Final-Gate (Handoff)

- **Workspace** (Runner + `frontend/dist` ohne Google Fonts): `gate_status: review_required`, Warnung `RESCUE_STICK_FINAL_REVIEW_COMPONENTS:package_list`
- **Runtime** (`/opt`, dist teils noch mit CDN): zusätzlich `frontend_bundle` review bis Operator-Redeploy

### Review-Entscheidungen (dokumentiert)

1. **Netzwerk-Stack:** Phase-1-Default **systemd-networkd**; NM optional; Live-OS-Test ausstehend → `package_list` bleibt review.
2. **Offline-Fonts:** Google-Fonts-Links aus `frontend/index.html` entfernt; Systemfont-Stack in `index.css`; **blocker_for_real_iso_build** wenn CDN in `/opt/…/dist/index.html`.
3. **systemd-Bind:** localhost-only; kein Auto-Restore/Partition beim Start.
4. **LAN:** local_only, LAN blockiert, Schreibaktionen über LAN blockiert, später Auth/Gate für LAN.

## Outputs

| Path | Purpose |
|------|---------|
| `build/rescue/emulation/rescue_stick_*.json` | Seven preview artifacts (lokal, nicht versioniert) |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json` | SHA256 manifest + scans |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json` | Aggregated gate |

## Verification

- Unit tests: `backend/tests/test_deploy_runner_rescue_stick_readonly_build_emulation_v1.py` (15 cases)
- Deploy docs: `docs/deploy/RESCUE_STICK_READONLY_BUILD_EMULATION_DE.md`

## Operator

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller` (Runner + frisches `frontend/dist`)
2. `POST /api/deploy/rescue-stick/build-emulation/run-all` mit `explicit_overwrite: true`
3. Final-Gate **ready** erst nach Live-OS-Netzwerk-Validierung und CDN-freiem dist auf Runtime

## Nächster Schritt

Redeploy → Runtime-`run-all` → Debian-Live-OS-Test für Netzwerk-Stack → dann ISO-Build-Auftrag (separat, Phase 0).
