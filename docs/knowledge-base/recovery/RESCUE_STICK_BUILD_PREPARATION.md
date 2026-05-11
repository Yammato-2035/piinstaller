# Rescue Stick — Build Preparation (KB)

Kurzüberblick zum **Setuphelfer Rettungsstick** in der Vorbereitungsphase: noch kein produktives ISO, kein USB-Flash, keine automatischen Reparaturen.

## Ziele dieser Phase

- Architektur und Live-OS-Basisentscheidung (Debian Live empfohlen).
- Inventar vorhandener vs. fehlender Komponenten.
- MVP-Scope-Gate ohne automatische Writes auf interne Platten.
- Debian-Live-Buildplan mit Ausgabe **nur** unter `build/rescue/`.
- ISO-Testmatrix (VM + Laptop; Pi/SecureBoot später).
- Build-Readiness-Gate über alle Handoff-JSONs.

## API

Siehe `docs/deploy/DEPLOY_RESCUE_STICK_BUILD_PREPARATION_DE.md` (bzw. `_EN.md`): `POST /api/deploy/rescue/...`.

## Skript

`scripts/rescue/build-rescue-iso.sh` — Template; Standardlauf ohne `live-build`-Build und ohne `dd`/`mkfs`/USB.

## Verwandt

- `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md`
- `docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`
- `docs/evidence/DEPLOY_RESCUE_STICK_BUILD_PREPARATION.md`
