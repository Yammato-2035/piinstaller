# Roadmap Delta — Rescue ISO Manual Operator Build

**2026-05-27** · **HEAD:** `11e27b6`

## Vorher → Nachher

| Element | Vorher | Nachher |
|---------|--------|---------|
| Phase-0-Gate | green | green (unverändert) |
| Rescue-Stick Bereich | blocked | **blocked** (kein ISO) |
| Verify | blocked | **blocked** (unverändert) |
| Operator-Build-Lauf | — | **policy blocked** Exit 30 |
| `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` | recommended_next | **blocked_by** `operator_terminal_no_tty` |

## Neue Evidence

- `rescue_iso_manual_operator_preflight_latest.json`
- `rescue_iso_operator_terminal_context_latest.json`
- `rescue_iso_manual_operator_build_classification_latest.json`
- `controlled_iso_build_latest_summary.json` (Wrapper)

## Nächster Prompt

**Primär:** `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` — im **echten Operator-Terminal** mit `sudo -v` wiederholen.

**Alternative:** `RESCUE_ISO_SUDOERS_ALLOWLIST_POLICY_DESIGN` — nur wenn organisatorisch kein interaktives sudo möglich.
