# Rescue stick — read-only build emulation (evidence)

**Date:** 2026-05-24  
**Runner:** `backend/deploy/runner_rescue_stick_readonly_build_emulation.py`
**Deploy baseline:** `bdd9865` (Finalize rescue stick build emulation gate)

## Exact bdd9865 Deploy Verification (2026-05-24)

| Punkt | Ergebnis |
|-------|----------|
| **Git HEAD** | `bdd9865` |
| **Offizieller Deploy** | Operator `sudo deploy-to-opt.sh` (vorherige Session Exit 0); Agent-Session: sudo nicht interaktiv — **Funktionsgleichheit:** Runner-SHA256 Workspace = `/opt`, Runtime-Gate Exit 0 |
| **Runtime-Gate** | Exit **0** (deploy_drift/Manifest OK) |
| **run-all** | `DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_READY`, `all_status: ready` |
| **CDN `/opt/frontend/dist`** | keine Google-Fonts-CDN |
| **Build-Artefakte** | keine ISO/IMG/QCOW2/squashfs/initrd/vmlinuz |
| **real_iso_build_allowed** | `false` |
| **live_os_network_test_pending** | `true` |
| **Nächstes Gate** | [Live-OS Network Validation](RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md) |

**Status:** Rescue stick read-only build emulation **green**; Live-OS network validation **review_required** (Host-Proxy only); Real ISO build **blocked**.

## Big Step — Temp Bundle + ISO Prep Gate (2026-05-24)

| Punkt | Status |
|-------|--------|
| Temp Bundle erzeugt/validiert | **green** (lokal, nicht versioniert) |
| Monolith-Gate | **review_required** — kein blocked |
| Phase 3 Entkopplung | **nicht ausgeführt** |
| Controlled ISO Prep Gate | **ISO_PREP_REVIEW_REQUIRED** |
| Live-OS Validation | **review_required** |
| `real_iso_build_allowed` | **false** |

Details: [RESCUE_BIG_STEP_STATUS_PLAN.md](RESCUE_BIG_STEP_STATUS_PLAN.md), [RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md](RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md)

## Temp Runtime Prep (2026-05-24)

| Punkt | Status |
|-------|--------|
| Bundle-Preview + IST | **green** (Doku) |
| `scripts/rescue-live/*` | local-only, kein sudo/apt/mount |
| Live-OS Validation | **review_required** (Hardware ausstehend) |
| `real_iso_build_allowed` | **false** |

Details: [RESCUE_LIVE_TEMP_RUNTIME_PREP_IST.md](RESCUE_LIVE_TEMP_RUNTIME_PREP_IST.md)

## Live-OS Network Validation Result (2026-05-24)

| Punkt | Ergebnis |
|-------|----------|
| **Scope** | Host-Runtime-Proxy auf `volker-ROG-Strix`, **kein** Rescue-Stick-Live-Boot |
| **Gesamtstatus** | **review_required** |
| **Backend/UI localhost** | **pass** (curl, 127.0.0.1-Bind) |
| **systemd-networkd / DHCP** | **not_tested** (Host: NetworkManager aktiv) |
| **CDN `/opt/dist`** | **pass** |
| **live_os_network_test_pending** | **true** (Handoff unverändert) |
| **real_iso_build_allowed** | **false** |

Details: [RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md](RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md)

## Hardware Live-Medium Validation (2026-05-24, Session 2)

| Punkt | Ergebnis |
|-------|----------|
| **Live-Medium gebootet** | **Nein** — persistenter Ubuntu-Host, kein `/lib/live/mount/medium` |
| **systemd-networkd / DHCP (Live)** | **not_tested** |
| **Gesamtstatus Hardware** | **review_required** |
| **real_iso_build_allowed** | **false** |

## Full Deploy + Package-List Validation (2026-05-24)

| Punkt | Ergebnis |
|-------|----------|
| **Vorheriger HEAD** | `f95acea` |
| **Offizieller Deploy** | `sudo ./scripts/deploy-to-opt.sh` — **OK** (Operator-Terminal, Exit 0) |
| **Runtime-Gate** | Exit **0** |
| **CDN `/opt/…/frontend/dist`** | Keine `fonts.googleapis.com` / `fonts.gstatic.com` |
| **OpenAPI** | **10** Routen |
| **run-all (Runtime)** | `DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_READY` |
| **Final-Gate** | **`ready`** — Emulation abgeschlossen |
| **package_list** | **`ok`** — systemd-networkd Phase-1-Default dokumentiert; `live_os_network_test_pending: true` |
| **real_iso_build_allowed** | **`false`** — kein ISO-Freigabe |
| **Verbotene Artefakte/Aktionen** | keine |

### Package-List Netzwerk (ohne apt)

| Feld | Wert |
|------|------|
| `default_network_stack` | systemd-networkd |
| `network_manager` | optional_later |
| `avahi/mDNS` | optional_later |
| `LAN-Zugriff` | blocked / default_off |
| `Web-UI` | local_only |
| `write_actions_over_lan` | blocked |
| `rescue_auth_required_for_lan` | true |
| `live_os_network_test_pending` | true (separates Hardware-Gate, nicht als erledigt behauptet) |

**Statusregel:** Emulation **grün/ready**; echter ISO-Build bleibt eigenes Gate nach Live-OS-Netzwerktest.

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

## Konsistenzlauf nach Runner-/Frontend-Redeploy (2026-05-24)

| Punkt | Ergebnis |
|-------|----------|
| **Commit** | `b204dee` — Runner-Preview-Entscheidungen versioniert |
| **Deploy** | Vollständiges `sudo deploy-to-opt.sh` in Agent-Session nicht möglich (sudo-Passwort); Runner + `frontend/dist/index.html` nach `/opt` (Gruppe `setuphelfer`), Backend-Neustart |
| **Runtime-Gate** | Exit **0** |
| **OpenAPI** | **10** Routen `rescue-stick/build-emulation/*` |
| **run-all (Runtime)** | `DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_REVIEW_REQUIRED` |
| **Final-Gate** | `review_required` — nur `package_list` (Live-OS-Netzwerktest ausstehend) |
| **frontend_bundle** | **ok** — `/opt/setuphelfer/frontend/dist/index.html` ohne Google-Fonts-CDN |
| **systemd / network** | **ok** (localhost, LAN blockiert, dokumentiert) |
| **Verbotene Artefakte** | keine ISO/IMG/QCOW2/squashfs/initrd/vmlinuz |
| **Verbotene Aktionen** | keine ausgeführt |

**Restpunkt:** `package_list` → `review_required` bis Debian-Live-OS-Validierung des Netzwerk-Stacks (`RESCUE_STICK_PKG_LIVE_OS_VALIDATION_PENDING`). Kein fake ready.

## Nächster Schritt

Debian-Live-OS-Netzwerktest (systemd-networkd) auf Hardware → danach separater ISO-Build-Auftrag mit Phase 0. **Kein ISO in diesem Auftrag.**
