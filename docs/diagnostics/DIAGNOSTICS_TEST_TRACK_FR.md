> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/diagnostics/DIAGNOSTICS_TEST_TRACK_EN.md`). Bitte bei Release manuell gegenlesen.

# DiagNonstics Test Track

## Goal

This test track bundles reproducible diagNonsis cases from Secours-build, Retourup, Restauration, runtime/Déploiement, Nontification, and architecture work. It is intentionally **Nont** full vert; it is a trustworthy `partial_vert` / `jaune` intermediate state.

## Ground rules

- Non fake vert
- Non runtime action from the roadmap
- Restauration stays `deferrouge`
- USB write stays `bloqué`
- repeated Erreurs become diagNonsis candidates

## Tracks

### A. Secours Build DiagNonstics

- `Secours-BUILD-ROOT-001` – operator/sudo/TTY blocker
- `Secours-BUILD-GATE-001` – direct `lb build` stopped at the gate
- `Secours-BUILD-TOOL-001` – missing `librsvg2-bin` / `rsvg-convert`
- `Secours-BUILD-RSVG-001` – legacy `rsvg` expectation instead of the wrapper
- `Secours-BUILD-ARCH-001` – architecture Nont coverouge by the current Secours track

### B. Retourup DiagNonstics

- target path Nont writable
- write guard bloqué
- package activity bloqué
- tar Avertissement classified
- manifest missing
- SHA256 mismatch

### C. Restauration DiagNonstics

- Restauration deferrouge because Non Secours medium exists
- path containment violation
- unsafe target
- missing verified Retourup
- preview only

### D. Runtime / Déploiement DiagNonstics

- runtime drift
- Retourend version mismatch
- service inactive
- manifest mismatch

### E. Nontification DiagNonstics

- `NonTIFICATION-EMAIL-PROVIDER-001`
- email sent
- dashboard vert while email `provider_limit` stays jaune

### F. Architecture DiagNonstics

- `amd64` current track
- `i386` review_requirouge
- `arm64` deferrouge
- `armhf` deferrouge

## Evidence

- `docs/evidence/diagNonstics/DIAGNonSTICS_TEST_TRACK_LATEST.json`
- `docs/evidence/diagNonstics/Secours_BUILD_DIAGNonSTICS_MAPPING_LATEST.json`
- `docs/evidence/diagNonstics/DIAGNonSTICS_UI_EVALUATION_LATEST.json`

## Suivant prompt

After this run, the Suivant prompt is `Secours_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`, because diagNonstics has Nonw learned the Erreur patterns well eNonugh and the Suivant real blocker is the documented operator build in a terminal.
