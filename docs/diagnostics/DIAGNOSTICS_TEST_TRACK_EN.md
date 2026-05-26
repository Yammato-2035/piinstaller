# Diagnostics Test Track

## Goal

This test track bundles reproducible diagnosis cases from rescue-build, backup, restore, runtime/deploy, notification, and architecture work. It is intentionally **not** full green; it is a trustworthy `partial_green` / `yellow` intermediate state.

## Ground rules

- no fake green
- no runtime action from the roadmap
- restore stays `deferred`
- USB write stays `blocked`
- repeated errors become diagnosis candidates

## Tracks

### A. Rescue Build Diagnostics

- `RESCUE-BUILD-ROOT-001` – operator/sudo/TTY blocker
- `RESCUE-BUILD-GATE-001` – direct `lb build` stopped at the gate
- `RESCUE-BUILD-TOOL-001` – missing `librsvg2-bin` / `rsvg-convert`
- `RESCUE-BUILD-RSVG-001` – legacy `rsvg` expectation instead of the wrapper
- `RESCUE-BUILD-ARCH-001` – architecture not covered by the current rescue track

### B. Backup Diagnostics

- target path not writable
- write guard blocked
- package activity blocked
- tar warning classified
- manifest missing
- SHA256 mismatch

### C. Restore Diagnostics

- restore deferred because no rescue medium exists
- path containment violation
- unsafe target
- missing verified backup
- preview only

### D. Runtime / Deploy Diagnostics

- runtime drift
- backend version mismatch
- service inactive
- manifest mismatch

### E. Notification Diagnostics

- `NOTIFICATION-EMAIL-PROVIDER-001`
- email sent
- dashboard green while email `provider_limit` stays yellow

### F. Architecture Diagnostics

- `amd64` current track
- `i386` review_required
- `arm64` deferred
- `armhf` deferred

## Evidence

- `docs/evidence/diagnostics/DIAGNOSTICS_TEST_TRACK_LATEST.json`
- `docs/evidence/diagnostics/RESCUE_BUILD_DIAGNOSTICS_MAPPING_LATEST.json`
- `docs/evidence/diagnostics/DIAGNOSTICS_UI_EVALUATION_LATEST.json`

## Next prompt

After this run, the next prompt is `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`, because diagnostics has now learned the error patterns well enough and the next real blocker is the documented operator build in a terminal.
