# Diagnostics Test Track

## Ziel

Diese Teststrecke bündelt reproduzierbare Diagnosefälle aus Rescue-Build-, Backup-, Restore-, Runtime-/Deploy-, Notification- und Architektur-Arbeit. Sie ist absichtlich **nicht** full green, sondern ein belastbarer `partial_green`-/`yellow`-Zwischenstand.

## Grundregeln

- kein Fake-Green
- keine Runtime-Aktion aus der Roadmap heraus
- Restore bleibt `deferred`
- USB-Write bleibt `blocked`
- wiederholbare Fehler werden zu Diagnosekandidaten

## Tracks

### A. Rescue Build Diagnostics

- `RESCUE-BUILD-ROOT-001` – Operator-/sudo-/TTY-Blocker
- `RESCUE-BUILD-GATE-001` – direktes `lb build` am Gate gestoppt
- `RESCUE-BUILD-TOOL-001` – `librsvg2-bin` / `rsvg-convert` fehlt
- `RESCUE-BUILD-RSVG-001` – Legacy-`rsvg` statt Wrapper
- `RESCUE-BUILD-ARCH-001` – Architektur nicht im aktuellen Rescue-Track

### B. Backup Diagnostics

- Zielpfad nicht schreibbar
- Write-Guard blockiert
- Package-Activity blockiert
- tar-Warnung klassifiziert
- Manifest fehlt
- SHA256-Mismatch

### C. Restore Diagnostics

- Restore bleibt ohne Rettungsmedium zurückgestellt
- Path-Containment-Verletzung
- unsicheres Ziel
- fehlendes verifiziertes Backup
- Preview-only

### D. Runtime / Deploy Diagnostics

- Runtime-Drift
- Backend-Version-Mismatch
- Service inaktiv
- Manifest-Mismatch

### E. Notification Diagnostics

- `NOTIFICATION-EMAIL-PROVIDER-001`
- E-Mail gesendet
- Dashboard grün, E-Mail `provider_limit` bleibt gelb

### F. Architecture Diagnostics

- `amd64` aktueller Track
- `i386` `review_required`
- `arm64` `deferred`
- `armhf` `deferred`

## Evidence

- `docs/evidence/diagnostics/DIAGNOSTICS_TEST_TRACK_LATEST.json`
- `docs/evidence/diagnostics/RESCUE_BUILD_DIAGNOSTICS_MAPPING_LATEST.json`
- `docs/evidence/diagnostics/DIAGNOSTICS_UI_EVALUATION_LATEST.json`

## Nächster Prompt

Nach diesem Lauf ist der nächste Prompt `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`, weil Diagnostics die Fehlerbilder jetzt ausreichend gelernt hat und der nächste echte Blocker der dokumentierte Operator-Build im Terminal ist.
