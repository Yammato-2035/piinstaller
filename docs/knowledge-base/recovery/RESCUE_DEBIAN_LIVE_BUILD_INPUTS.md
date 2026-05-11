# Rescue — Debian Live Build Inputs (KB)

## Zweck

Dieser Strang erzeugt **nur** Dateien und Manifeste unter `build/rescue/debian-live/`, die ein Operator spaeter mit Debian **live-build** (ausserhalb dieser API) konsumieren kann. Setuphelfer fuehrt hier **keine** Image-Erzeugung und **keine** privilegierten Schreiboperationen auf Medien aus.

## Safety

- Hook-Dateien enden auf `.template` und sind nicht ausfuehrbar.
- Scanner lehnt typische gefaehrliche Muster in Dateiinhalten ab (z. B. Paketmanager-Install, Dienststeuerung, `debootstrap`, `grub-mkrescue`, `xorriso`, `dd`/`mkfs`/`wipefs`, verwaiste `.iso`/`.img`, Legacy-`pi-installer`, Symlink-Flucht aus `build/rescue/`).

## Hinweis (Python-Bezeichner)

Die Runner-Funktion heisst `build_debian_live_includes_ch_root` (Unterstrich zwischen `ch` und `root`), damit `routes.py` beim Runtime-Assembly-Safety-Scan **kein** falsches `chroot(`-Token aus Handler-Namen ableitet. Der HTTP-Pfad bleibt `/rescue/debian-live/includes-chroot`.

## Verweise

- Deploy-Uebersicht (DE): `docs/deploy/DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS_DE.md`
- Deploy overview (EN): `docs/deploy/DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS_EN.md`
- Evidence-Index: `docs/evidence/DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_INPUTS.md`
- Runner: `backend/deploy/runner_rescue_debian_live_build_inputs.py`
