# R.8 — Rebuild After Clean Result

**Datum:** 2026-06-13  
**Kampagne:** R.8-BUILD-UNBLOCK

## Zusammenfassung

ISO-Rebuild **nicht gestartet** — Operator-sudo-Clean fehlgeschlagen (kein interaktives Terminal).

## Phasen

| Phase | Ergebnis |
|-------|----------|
| 0 Blocker dokumentiert | **ja** (`R8_BUILD_PERMISSION_BLOCKER.md`) |
| 1 Dry-run plausibel | **ja** (15 Pfade, nur Build-Tree) |
| 2 Clean execute | **nein** — sudo Passwort erforderlich |
| 3 Prepare + Validate | **übersprungen** / Validate weiterhin **11** |
| 4 R6 Quick Check | **PASS** (Tree-Inhalt korrekt) |
| 5 ISO Build | **nicht gestartet** |
| 6 Post-Build | **n/a** |

## LB_EXIT

| Versuch | LB_EXIT | error_code |
|---------|---------|------------|
| Build (diese Kampagne) | — | nicht gestartet |
| Permission preflight | **34** | `rescue_iso_build.permission_denied_dot_build` |
| Policy guard (Agent) | **30** | `blocked_requires_operator_sudo_policy` |

## root-owned nach Clean

**ja** — ~64561 Einträge (unverändert)

## Nächste Aktion (Operator, interaktives Terminal)

```bash
cd /home/volker/piinstaller

# 1. Clean
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
find build/rescue/live-build/setuphelfer-rescue-live -user root | wc -l

# 2. Re-prepare + validate
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
# Erwartung: Exit 0

# 3. ISO Build
export OPERATOR_ISO_BUILD_FREIGABE=1
export SETUPHELFER_RESCUE_BUILD_PROFILE=standard
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile standard \
  --run-id r8_clean_$(date -u +%Y%m%d_%H%M%S)
```

Danach: SquashFS R6-Check → `ready_for_r8_usb_write` (separate Kampagne).

## Verbotene Aktionen

Kein USB-Write, MSI-Boot, Deploy — eingehalten.
