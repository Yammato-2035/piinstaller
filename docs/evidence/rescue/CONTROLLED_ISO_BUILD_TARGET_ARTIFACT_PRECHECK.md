# Controlled ISO Build — Target Artifact Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Architektur

Quelle: `rescue_target_architecture_matrix_latest.json`

| Ziel | Status |
|------|--------|
| **amd64** / x86_64 | **primary_candidate** |
| i386 | review_required (nicht aktiv) |
| arm64/armhf | deferred |

Host: `x86_64` → **amd64** konsistent.

## Erwartetes Artefakt (nach Build)

`build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`

## Prior-Artefakte (nicht als neuer Build werten)

| Datei | Anmerkung |
|-------|-----------|
| `binary.hybrid.iso` (~512 MB, 2026-06-01) | **Prior-Build** — Preflight inventarisiert 28 Prior-Artefakte |
| `binary/live/filesystem.squashfs` | Stale — Cleanup vor Neu-Build |

Kein versehentliches i386/arm-Target in Tree-Konfiguration (amd64 Live-Build).
