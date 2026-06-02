# QEMU Guest Agent Smoke — Phase 0

**Datum:** 2026-06-02  
**HEAD:** `c70bfe1`  
**Branch:** `main`  
**Runtime-Profil:** `release`  
**profile_gate_status:** `green`

## ISO-Fingerprint

| Feld | Wert |
|------|------|
| ISO-Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| ISO-Größe | 511705088 B |
| ISO-SHA256 | `505989f7d348265c08e8baeaa2971f81aa855224223859ae8d536b984dafaf52` |
| ISO-Fingerprint ok | **yes** |

## Smoke-Freigabe

| Feld | Wert |
|------|------|
| qemu_smoke_allowed (Agent-Session) | **no** — Phase 2 blockiert (`sudo` Passwort erforderlich) |
| Operator-Skript bereit | **yes** — `scripts/rescue-live/qemu-guest-agent-smoke-operator.sh` |

Dieser Agent-Lauf führt **keinen** QEMU-Start aus (STRICT: kein QEMU ohne `local_lab`).
