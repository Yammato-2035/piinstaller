# Deploy — Rescue ISO Artefakt-Vorbereitung (DE)

## Zweck

Erzeugt eine **reale, aber nicht bootfähige** Artefaktstruktur unter `build/rescue/` für eine spätere Debian-Live-basierte Rescue-ISO: simuliertes RootFS-Layout, Frontend-/Backend-Manifeste (Analyse, kein Build), geplante Boot-Verzeichnisse (nur `.planned`/`.placeholder`), Overlay-/Persistenz-Strategie als JSON und ein **Readiness-Gate**-Handoff unter `docs/evidence/runtime-results/handoff/`.

## API

| Methode | Pfad |
|---------|------|
| `POST` | `/api/deploy/rescue/artifact/rootfs` |
| `POST` | `/api/deploy/rescue/artifact/frontend` |
| `POST` | `/api/deploy/rescue/artifact/backend` |
| `POST` | `/api/deploy/rescue/artifact/boot-structure` |
| `POST` | `/api/deploy/rescue/artifact/overlay-strategy` |
| `POST` | `/api/deploy/rescue/artifact/readiness-gate` |

Rückgabe-Codes: `DEPLOY_RESCUE_ARTIFACT_ROOTFS_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (analog für `ARTIFACT_FRONTEND`, `ARTIFACT_BACKEND`, `ARTIFACT_BOOT_STRUCTURE`, `ARTIFACT_OVERLAY_STRATEGY`). Finales Gate: `DEPLOY_RESCUE_ARTIFACT_READINESS_GATE_READY`, `_REVIEW_REQUIRED` oder `_BLOCKED`.

Body: wie bei anderen Deploy-Rescue-Endpunkten, Feld `explicit_overwrite` (bool).

## Verbote (Strict Mode)

Kein echtes ISO-Image, kein `grub-mkrescue`, kein `xorriso`, kein `dd`, kein `mkfs`, kein USB-/PXE-Write, kein Release/Publish, kein Installer-Execute. Schreibpfade: nur kontrolliert unter `build/rescue/` (Manifeste/Struktur) und das Gate-JSON unter `docs/evidence/…/handoff/` (keine `.iso`/`.img` außerhalb des optional ignorierten `build/rescue/output/` für Alt-Artefakte).

## Version

Nach grüner Testkette und operativer Sichtung manuell **1.8.0** erwägen; kein automatischer Bump.
