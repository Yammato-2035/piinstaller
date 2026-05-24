# Rescue stick — read-only build emulation (KB)

## Purpose

Prepare a **complete emulation pass** before any real Debian live / ISO work. All outputs are JSON under `build/rescue/emulation/` and `docs/evidence/runtime-results/handoff/` with:

- `generated: false`
- `readonly_emulated: true`
- `no_real_build_execution: true`

## Runner

`backend/deploy/runner_rescue_stick_readonly_build_emulation.py`

## Gates

Contract: `docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md`

Final handoff: `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json`

## Next step

Run prompt `docs/prompts/PROMPT_RESCUE_STICK_READONLY_BUILD_EMULATION.md` follow-up only if extending emulation; real ISO requires a **separate** gated task.
