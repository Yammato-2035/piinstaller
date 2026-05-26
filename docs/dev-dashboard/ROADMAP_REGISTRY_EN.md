# Dev Dashboard Roadmap Registry

## Purpose

The roadmap registry in the Setuphelfer Development Dashboard is not a plain to-do list and not an execute module. It is a read-only control, documentation, and prompt-preparation module.

## Why a simple to-do list is not enough

A plain to-do list does not answer:

- what is actually proven
- which areas are only partially green
- which blockers freeze multiple follow-up tracks at once
- why certain topics were consciously deferred
- which Cursor prompt is the next sensible step

The registry therefore combines areas, milestones, tasks, blockers, decisions, notes, evidence, and next prompts.

## Status values

- `green`: trustworthily implemented and proven
- `partial_green`: substantial progress, but not fully approved
- `yellow`: in progress or only partially trustworthy
- `blocked`: blocked by technical or factual constraints
- `deferred`: consciously postponed
- `unknown`: not provable
- `deprecated`: no longer an active track

## Why restore is deferred

Restore end-to-end remains consciously deferred while no bootable rescue medium and no non-production target system are available. This is a safety decision, not optimism.

## Why diagnostics is not fully green

Diagnostics already has catalog, API, and structure pieces. It would be fully green only with real error-case tracks, UI evaluation, and a trustworthy evidence matrix.

## How the next prompt is computed

Selection prioritizes:

1. missing proof that blocks multiple areas
2. recurring dashboard ambiguity
3. safety/gate work before risky runtime work
4. prepared architecture without enough evidence
5. no marketing/cloud/HostPilot prioritization before recovery core is green

## Why the dashboard does not execute runtime actions

The roadmap registry only shows:

- status
- reasons
- blockers
- evidence
- the next sensible prompt

It does not start backups, restores, rescue builds, deploys, or backend restarts.

## Evidence and notes

- Evidence links point to the trustworthy sources for an area.
- Notes are for factual context, not hidden status manipulation.

## Prompt export

The prompt export generates a STRICT MODE text with:

- goal
- non-goals
- safety rules
- the Phase 0 gate
- concrete tasks
- allowed areas
- forbidden actions
- tests
- docs/FAQ/i18n targets
- the closing report
