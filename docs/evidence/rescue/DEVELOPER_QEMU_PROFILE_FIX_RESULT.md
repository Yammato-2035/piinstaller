# Developer QEMU Profile Fix — Result Summary

**Datum:** 2026-06-02  
**Auftrag:** STRICT MODE — Serial + Agent Autostart für Developer-QEMU-ISO vorbereiten (kein Build/QEMU/USB)

## Ergebnis

| Aspekt | Status |
|--------|--------|
| Profil-Fix umgesetzt | yes |
| Prepare Exit 0 | yes |
| Validate Exit 0 | **no** (11 — stale root-owned binary/) |
| ISO gebaut | **no** |
| QEMU ausgeführt | **no** |
| Readiness | **review_required** |

## Root Cause (vorher)

Operator-QEMU-Smoke `qemu_rescue_developer_autopilot_20260602_202725` gegen **Standard-ISO**: Serial 0 B, Autopilot nicht enabled, `guest_report_missing`.

## Fix (Variante A)

- `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu` materialisiert Serial-Bootappend + Hook 090
- Autopilot-Preflight-Guard verhindert erneuten Profil-Mismatch
- Standard-ISO unverändert defensiv

## Bootappend

| | Inhalt |
|---|--------|
| **Vorher (Standard)** | `quiet splash init=/lib/systemd/systemd` |
| **Nachher (developer-qemu Prepare)** | `init=/lib/systemd/systemd console=tty0 console=ttyS0,115200n8 …` |

## Services

- Autopilot: Hook 090 enable beim Chroot-Build
- Dev-Agent: bewusst **nicht** separat enabled (Autopilot-Unit)

## Offene Punkte

1. Validate Exit 11 — Operator `sudo ./auto/clean` vor Rebuild
2. QEMU Guest Agent Smoke bleibt **blocked** bis neues developer-qemu-ISO + Smoke
3. Rescue bleibt nicht grün ohne Boot-/Agent-Nachweis

## Evidence-Dateien

- `DEVELOPER_QEMU_PROFILE_FIX_PHASE0.md`
- `DEVELOPER_QEMU_PROFILE_CONFIG_REVIEW.md`
- `DEVELOPER_QEMU_SERVICE_AUTOSTART_REVIEW.md`
- `DEVELOPER_QEMU_AGENT_BUNDLE_REVIEW.md`
- `DEVELOPER_QEMU_PROFILE_FIX_DECISION.md`
- `DEVELOPER_QEMU_PROFILE_FIX_STATIC_TEST_RESULT.md`
- `DEVELOPER_QEMU_PROFILE_FIX_PREPARE_VALIDATE_RESULT.md`
- `developer_qemu_profile_fix_latest.json`

## Nächster Schritt

**DEVELOPER QEMU ISO REBUILD OPERATOR RUN** → danach **QEMU GUEST AGENT SMOKE, NO USB**
