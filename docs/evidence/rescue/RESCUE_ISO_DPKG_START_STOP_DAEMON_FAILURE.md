# Rescue ISO DPKG Start-Stop-Daemon Failure

**Datum:** 2026-05-25
**Status:** runtime_verified_prebuild_green

## Fehlerbild

Der erste kontrollierte ISO-Build lief in `live-build` mit `LB_EXIT=100` aus. Der relevante Befund war:

- `dpkg: warning: 'start-stop-daemon' not found in PATH or not executable`

## Ursache

Die produktive Rescue-ISO-Strecke pruefte den problematischen Zustand vor dem Build nicht explizit.
Dadurch wurde ein chroot-/dpkg-Problem erst waehrend `live-build` sichtbar, obwohl der Build in diesem Strict-Mode gar nicht wiederholt werden sollte.

## Fix im Workspace

- neues read-only Skript `scripts/rescue-live/validate-live-build-dpkg-preflight.sh`
- Einbindung in:
  - `scripts/rescue-live/validate-controlled-live-build-tree.sh`
  - `backend/core/rescue_iso_build_executor.py`
  - `backend/core/rescue_iso_build_state.py`
- Dashboard-/Executor-Status fuer `dpkg_preflight`
- Tests fuer ok/review_required/blocked ohne `lb build`, `apt` oder Root-Aktion

## Lokaler Verifikationsstand

- Green-Up-/Rescue-Unit-Tests gruen
- lokale Preflight-Kette meldet `ok` bzw. `pre_chroot_ok`, sofern kein fertiger chroot vorliegt
- keine Freigabe fuer echten ISO-Build abgeleitet

## Produktive Runtime-Abnahme

Nach den finalen Helper-Deploys ist die Runtime-Abnahme fuer den Prebuild-Pfad abgeschlossen:

- letzter erfolgreicher Job: `deploy-20260525T193756Z-954998`
- `deploy_exit_code = 0`
- `runtime_gate_exit_after = 0`
- SHA256 Workspace == `/opt` fuer:
  - `backend/core/rescue_iso_build_executor.py`
  - `backend/core/rescue_iso_build_state.py`
- Runtime-Smokes:
  - `GET /api/dev-dashboard/rescue-iso/status` → `status = green`
  - `dpkg_preflight` → `ok`
  - `prepare_bundle` → `ok`
  - `validate_bundle` → `ok`
  - `prepare_tree` → `ok`
  - `validate_tree` → `ok`
- `dpkg_preflight.status = pre_chroot_ok`
- `usb_write.allowed = false`

Damit ist der DPKG-Preflight in der produktiven Runtime verifiziert, ohne einen neuen ISO-Build zu starten.

## Verbotene Aktionen weiterhin nicht ausgefuehrt

- kein ISO-Build
- kein `lb build`
- kein USB-Write
- kein `dd`
- kein `mkfs`
- kein `parted write`
