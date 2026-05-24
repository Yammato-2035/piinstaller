# Rettungsstick – Read-only Build-Gate (Vertrag)

**Version:** 1.0 (Dokumentation)  
**Bezug:** Partitions-Handoff `RESCUE_STICK_PARTITION_HANDOFF.md`, Finalisierung `ffd2d8a`

## Zweck

Definiert die **Pflicht-Gates**, bevor der Setuphelfer Rettungsstick in einen **echten** ISO-/Live-Build (`lb build`, debootstrap, chroot, apt, Stick-Write) gehen darf.

Bis alle Gates **green** sind: nur Read-only Emulation, Handoffs, Previews.

## Pflicht-Gates (alle green erforderlich)

| # | Gate | Nachweis |
|---|------|----------|
| 1 | **Runtime-Gate** | `./scripts/check-runtime-deploy-gate.sh` Exit 0 |
| 2 | **Partitionshelfer final read-only** | `docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md` Status green |
| 3 | **Backup/Verify/Restore-Preview** | Rescue/Backup-Runner-Handoffs ohne blocked; kein Auto-Restore |
| 4 | **Rescue-Handoff** | `handoff_sources` aus Partitions-API + `RESCUE_STICK_PARTITION_HANDOFF.md` |
| 5 | **Debian-Live-Basis** | `rescue_live_os_base_decision.json` → `debian_live` |
| 6 | **Paketliste** | Definiert in `rescue_debian_live_build_plan.json` / Inputs-Handoff |
| 7 | **Setuphelfer Runtime-Bundle** | `rescue_runtime_bundle_manifest` + Seal, keine Host-Pfade |
| 8 | **Keine Secrets im Bundle** | Branding/Secret-Guard-Handoff |
| 9 | **Keine Host-Pfade im Bundle** | Sandbox-Manifest, allowlist-konform |
| 10 | **Kein Legacy-piinstaller-Branding** | `setuphelfer_branding_guard_check.json` |
| 11 | **Kein Write-Default** | MVP-Scope: `forbidden_auto_operations_absent` |
| 12 | **Gefährliche Live-Aktionen gated** | rescue_hardstop, write_guard, restore_gate |
| 13 | **Kein automatisches Restore** | `restore_execution_allowed=false` in Previews |
| 14 | **Kein automatisches Partitionieren** | Partitions Queue/Apply Stub |
| 15 | **Evidence-Pfade** | `docs/evidence/runtime-results/handoff/rescue_*.json` + `build/rescue/` |

## Erlaubt vor Gate-Freigabe

- `runner_rescue_build_environment_emulation` (simulated workspace)
- `runner_rescue_build_readiness_gate` (read-only Bewertung)
- Paketlisten-**Preview**, systemd-**Preview**, Frontend/Backend-Bundle-**Preview**
- Evidence-Manifeste unter `build/rescue/emulation/`

## Verboten vor Gate-Freigabe

`lb build`, debootstrap, chroot, `apt install`/`upgrade`, mount/umount für Stick-Provisioning, ISO-Erzeugung (xorriso/grub-mkrescue), `dd` auf Geräte, qemu-Boot als Produktivnachweis, automatischer Restore/Partition-Write.

## Freigabe-Workflow (Operator)

1. Alle 15 Gates prüfen (Handoff-JSON + Runtime-Gate + UI-Smoke).
2. `rescue_build_readiness_gate` Status dokumentieren.
3. Erst danach separater Auftrag „echter ISO-Build“ mit erneutem Phase-0-Gate.

## Post-Deploy Emulation (2026-05-24, Commit `60e3f31`)

| Thema | Entscheidung | Final-Gate |
|-------|----------------|------------|
| **Netzwerk-Stack (Live-OS)** | Phase 1: **systemd-networkd** als Default; NetworkManager **optional_later**; Live-OS-Validierung noch **pending** | `package_list` → **review_required** bis Live-Test |
| **Offline-Fonts / CDN** | Rescue ohne CDN-Pflicht: **Systemfonts**; `frontend/index.html` ohne Google Fonts (Rebuild `dist` nötig) | Runtime `/opt` dist ggf. noch alt → `frontend_bundle` review bis Redeploy |
| **systemd-Service-Bind** | Backend `127.0.0.1:8000`, UI `127.0.0.1:3001`; kein Auto-Restore/Partition; LAN erst mit Rescue-LAN-Gate | Emulation: **ok** |
| **LAN-Policy** | `default: local_only`, `lan_access: blocked`, `write_actions_over_lan: blocked`, `rescue_auth_required_for_lan: true` | Emulation: **ok** |

**Emulation-Final-Gate (Full Deploy 2026-05-24):** **`ready`** — `live_os_network_test_pending: true`, `real_iso_build_allowed: false`. Kein fake ready für ISO.

## Exact bdd9865 Deploy Verification

- Runtime-Gate Exit 0; run-all **READY**; CDN-frei in `/opt`; keine Build-Artefakte.
- **Nächstes Pflicht-Gate vor ISO:** Live-OS Network Validation — Plan `docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md`, Runbook `docs/runbooks/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RUNBOOK.md`.

## Live-OS Network Validation Result (2026-05-24)

| Feld | Wert |
|------|------|
| **Evidence** | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` |
| **Gesamtstatus** | **review_required** (Host-Proxy Session 1; **Hardware Live-Medium Session 2: nicht gebootet**) |
| **live_os_network_test** | **not passed** — systemd-networkd/DHCP auf Live-Medium ausstehend |
| **real_iso_build_allowed** | **false** |
| **next_gate** | Hardware-Live-Boot mit systemd-networkd, dann ISO dry-run / controlled ISO prep |

**Host-Proxy bestätigt:** Backend/UI localhost, 127.0.0.1-Bind, CDN-frei unter `/opt`. **Offen:** DHCP systemd-networkd auf gebootetem Live-Medium mit Temp-Runtime.

## Temp Runtime Prep (2026-05-24)

| Artefakt | Status |
|----------|--------|
| `RESCUE_LIVE_TEMP_RUNTIME_PREP_IST.md` | IST-Stand |
| `RESCUE_TEMP_RUNTIME_BUNDLE_PREVIEW.md` | Bundle **ok** (Preview) |
| `scripts/rescue-live/*` | local-only Start/Check |
| `RESCUE_STICK_TEMP_RUNTIME_ON_LIVE_MEDIUM_RUNBOOK.md` | Operator-Runbook |
| Result-Template | Evidence-Vorlage |

**Temp Runtime Prep:** **green**. **Live-OS Validation:** **review_required**. **real_iso_build_allowed:** **false**.

## Referenzen

- `docs/evidence/rescue/RESCUE_STICK_READONLY_BUILD_GATE_IST.md`
- `docs/evidence/rescue/RESCUE_STICK_READONLY_BUILD_EMULATION.md`
- `docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md`
- `docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md`
- `docs/runbooks/RESCUE_STICK_TEMP_RUNTIME_ON_LIVE_MEDIUM_RUNBOOK.md`
- `docs/evidence/rescue/RESCUE_LIVE_TEMP_RUNTIME_PREP_IST.md`
- `docs/prompts/PROMPT_RESCUE_STICK_READONLY_BUILD_EMULATION.md`
