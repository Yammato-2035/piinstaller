# Rescue ISO — Artefakt-Vorbereitung (Strict)

## Kurzbeschreibung

Diese Phase materialisiert **keine** bootfähige ISO. Sie legt unter `build/rescue/` ein nachvollziehbares Layout und JSON-Manifeste an, damit RootFS-Pfade, Offline-Frontend-Referenzen, Backend-Routen-Nachweise, geplante Boot-Komponenten und eine Overlay-Strategie **ohne** `xorriso`/`grub-mkrescue`/`dd` dokumentiert und per API auslösbar sind.

## Artefakte

| Relativer Pfad | Inhalt |
|----------------|--------|
| `build/rescue/rootfs/` | Verzeichnisse unter `opt|etc|var/log|run|usr/share/.../setuphelfer` mit Platzhalterdatei |
| `build/rescue/rootfs_manifest.json` | Erwartete Pfade, Overlay-Definition (lower/upper), Evidence-Pfade |
| `build/rescue/frontend_manifest.json` | Präsenz von `frontend/dist/index.html` und `assets/`, Asset-Liste, Legacy-Check |
| `build/rescue/backend_manifest.json` | Checks gegen `backend/app.py`, `routes.py`, Rescue-/Verify-/Preview-Hinweise |
| `build/rescue/boot/`, `EFI/`, `live/` | Nur geplante Textdateien (keine Binär-Bootloader) |
| `build/rescue/boot_artifact_manifest.json` | Geplante GRUB/EFI/Squashfs/initrd/Kernel-Placeholder |
| `build/rescue/overlay_persistence_strategy.json` | readonly lower, tmpfs upper, keine Auto-Persistenz auf Zielplatten |
| `docs/evidence/runtime-results/handoff/rescue_artifact_readiness_gate.json` | Aggregation inkl. `rescue_iso_final_readiness_gate.json` und Branding-Handoff |

## Gate-Status

- **ready**: alle Manifeste vorhanden, keine Blocker (Branding ok, keine verbotenen Images unter `build/rescue/`, keine Legacy-Strings in Manifesten).
- **review_required**: z. B. fehlendes ISO-Final-Handoff oder Frontend-Dist-Hinweise.
- **blocked**: Branding blockiert, Recovery-/Manifest-Lücken, verbotene Images, Legacy in Manifest-JSON.

## Verwandte Dokumentation

- `docs/deploy/DEPLOY_RESCUE_ISO_ARTIFACT_PREPARATION_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_RESCUE_ISO_ARTIFACT_PREPARATION.md`
- Runner: `backend/deploy/runner_rescue_iso_artifact_preparation.py`
