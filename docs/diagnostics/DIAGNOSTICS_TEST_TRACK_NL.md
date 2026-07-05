> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/diagnostics/DIAGNOSTICS_TEST_TRACK_EN.md`). Bitte bei Release manuell gegenlesen.

# DiagNeestics Test Track

## Goal

This test track bundles reproducible diagNeesis cases from roodding-build, Terugup, Herstel, runtime/Deploy, Neetification, and architecture work. It is intentionally **Neet** full groen; it is a trustworthy `partial_groen` / `geel` intermediate state.

## Ground rules

- Nee fake groen
- Nee runtime action from the roadmap
- Herstel stays `deferrood`
- USB write stays `geblokkeerd`
- repeated Fouts become diagNeesis candidates

## Tracks

### A. roodding Build DiagNeestics

- `roodding-BUILD-ROOT-001` – operator/sudo/TTY blocker
- `roodding-BUILD-GATE-001` – direct `lb build` stopped at the gate
- `roodding-BUILD-TOOL-001` – missing `librsvg2-bin` / `rsvg-convert`
- `roodding-BUILD-RSVG-001` – legacy `rsvg` expectation instead of the wrapper
- `roodding-BUILD-ARCH-001` – architecture Neet coverood by the current roodding track

### B. Terugup DiagNeestics

- target path Neet writable
- write guard geblokkeerd
- package activity geblokkeerd
- tar Waarschuwing classified
- manifest missing
- SHA256 mismatch

### C. Herstel DiagNeestics

- Herstel deferrood because Nee roodding medium exists
- path containment violation
- unsafe target
- missing verified Terugup
- preview only

### D. Runtime / Deploy DiagNeestics

- runtime drift
- Terugend version mismatch
- service inactive
- manifest mismatch

### E. Neetification DiagNeestics

- `NeeTIFICATION-EMAIL-PROVIDER-001`
- email sent
- dashboard groen while email `provider_limit` stays geel

### F. Architecture DiagNeestics

- `amd64` current track
- `i386` review_requirood
- `arm64` deferrood
- `armhf` deferrood

## Evidence

- `docs/evidence/diagNeestics/DIAGNeeSTICS_TEST_TRACK_LATEST.json`
- `docs/evidence/diagNeestics/roodding_BUILD_DIAGNeeSTICS_MAPPING_LATEST.json`
- `docs/evidence/diagNeestics/DIAGNeeSTICS_UI_EVALUATION_LATEST.json`

## Volgende prompt

After this run, the Volgende prompt is `roodding_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`, because diagNeestics has Neew learned the Fout patterns well eNeeugh and the Volgende real blocker is the documented operator build in a terminal.
