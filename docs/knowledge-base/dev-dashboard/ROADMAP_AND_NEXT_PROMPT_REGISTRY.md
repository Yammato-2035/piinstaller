# Roadmap and Next Prompt Registry

## What it is

The Setuphelfer Development Dashboard roadmap registry is a read-only source of truth for:

- roadmap areas
- milestones and tasks
- blockers and decisions
- evidence links
- the recommended next Cursor prompt

## What it is not

- not a backup launcher
- not a restore launcher
- not a rescue execute path
- not a deploy helper
- not a way to force areas green

## Core principles

1. `green` needs evidence.
2. `partial_green` and `yellow` stay visible when work is only partially proven.
3. `blocked` and `deferred` must explain why.
4. Restore stays deferred until safe prerequisites exist.
5. Diagnostics stays partially green until real error tracks and UI evidence exist.
6. Every closing report must state dashboard progress, diagnostics learning progress, evidence files, the next prompt decision, non-executed actions, and the remaining blocked/deferred state.
7. Repeated errors are no longer “just findings”; they become diagnosis candidates with matcher, recommendation, evidence, and test coverage.

## Next Prompt Registry

The next-prompt registry exists to stop repeated findings from floating around without a concrete follow-up. Every prompt entry documents:

- why it is relevant
- what blocks it
- what it unlocks
- what outputs are expected
- which safety rules apply

## Prompt export

The export endpoint returns a plain STRICT MODE prompt text suitable for copy/paste into Cursor. The exported text is documentation and planning guidance only; it never triggers runtime actions by itself.

## Closure discipline

The registry is only trustworthy when it is kept in sync with real evidence. That means:

- no area turns `green` without tests, runtime smokes, or hardware/E2E proof
- evidence files must be cited in the closing report
- roadmap, next-prompt selection, and blocker lists must be reviewed whenever a run learns something new
