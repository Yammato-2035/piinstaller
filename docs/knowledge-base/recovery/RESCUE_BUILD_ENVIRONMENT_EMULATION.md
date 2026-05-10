# Rescue Build Environment Emulation (KB)

## Zweck

Die Pipeline simuliert eine **vollstaendige** Debian-Live-Build-Umgebung (Verzeichnisse, erwartete Artefakte, Log-Stufen), **ohne** echte Build-Tools oder binaere ISO/SquashFS-Erzeugung. Alle Outputs sind Metadaten mit `readonly_emulated: true` und `generated: false`.

## Warum keine echte ISO

Emulation dient Konsistenzpruefung, Gates und Evidence — echte Images erfordern live-build, Rootfs-Pack und Boot-Image-Tools, die hier bewusst ausgeschlossen sind.

## Verweise

- `docs/deploy/DEPLOY_RESCUE_BUILD_ENVIRONMENT_EMULATION_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_RESCUE_BUILD_ENVIRONMENT_EMULATION.md`
- Runner: `backend/deploy/runner_rescue_build_environment_emulation.py`
