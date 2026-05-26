# Rescue Build Diagnostics

## Zweck

Diese Diagnose-Notiz trennt die aktuellen Rescue-Build-Blocker sauber voneinander, damit das Dashboard und die Evidence keinen generischen "Build fehlgeschlagen"-Eindruck erzeugen.

## RESCUE-BUILD-ROOT-001

- Titel DE: `Rescue-ISO-Build benötigt kontrollierte Root-Ausführung`
- Titel EN: `Rescue ISO build requires controlled root execution`
- Typische Signale:
  - `blocked_requires_operator_sudo_policy`
  - `sudo: ein Terminal ist erforderlich`
  - `sudo: a terminal is required`
  - `sudo: a password is required`
  - `LB_EXIT=1` oder Wrapper-Policy-Exit ohne ISO-Artefakt nach sudo-Block
- Bedeutung:
  - Toolchain, `rsvg` und Live-Build-Tree koennen vorbereitet sein.
  - Der echte Build bleibt trotzdem blockiert, solange kein sicherer Root-Pfad dokumentiert ist.
- Empfehlung:
  - Wrapper aus einem echten Operator-Terminal mit sudo-Rechten starten
  - oder eng begrenzte dokumentierte sudo-Allowlist fuer genau den freigegebenen Wrapper vorbereiten
  - kein Passwort via stdin, kein Askpass-Hack, kein globales `NOPASSWD`

## RESCUE-BUILD-GATE-001

- Titel DE: `Direkter lb build wurde durch kontrolliertes Build-Gate blockiert`
- Titel EN: `Direct lb build was blocked by the controlled build gate`
- Typische Signale:
  - `blocked_controlled_build_gate_required`
  - `Use controlled gate before running lb build.`
  - Exit `20` aus `auto/build`
- Bedeutung:
  - `auto/build` ist absichtlich ein Stop-Script.
  - Zulaessig bleibt nur der kontrollierte Wrapper-/`noauto`-Pfad.

## RESCUE-BUILD-ARCH-001

- Titel DE: `Zielarchitektur nicht durch aktuellen Build abgedeckt`
- Titel EN: `Target architecture is not covered by the current build track`
- Bedeutung:
  - `amd64` ist der aktuelle aktive Rescue-ISO-Track.
  - `i386` bleibt separater Review-Track.
  - `arm64` und `armhf` bleiben getrennte Image-/Provisioning-Tracks.

## Verknuepfte Dokumentation

- `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
- `docs/knowledge-base/recovery/RESCUE_ISO_CONTROLLED_BUILD_GATE.md`
- `docs/architecture/RESCUE_TARGET_ARCHITECTURE_MATRIX.md`
