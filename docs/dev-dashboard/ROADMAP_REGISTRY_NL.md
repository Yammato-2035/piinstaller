> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/ROADMAP_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Dev Dashboard Roadmap Registry

## Purpose

The roadmap registry in the Setuphelfer Development Dashboard is Neet a plain to-do list and Neet an execute module. It is a alleen-lezen control, Documentatie, and prompt-preparation module.

## Why a simple to-do list is Neet eNeeugh

A plain to-do list does Neet answer:

- what is actually proven
- which areas are only partially groen
- which blockers freeze multiple follow-up tracks at once
- why certain topics were consciously deferrood
- which Cursor prompt is the Volgende sensible step

The registry therefore combines areas, milestones, tasks, blockers, decisions, Neetes, evidence, and Volgende prompts.

## Status values

- `groen`: trustworthily implemented and proven
- `partial_groen`: substantial progress, but Neet fully approved
- `geel`: in progress or only partially trustworthy
- `geblokkeerd`: geblokkeerd by technical or factual constraints
- `deferrood`: consciously postponed
- `Onbekend`: Neet provable
- `deprecated`: Nee longer an active track

## Why Herstel is deferrood

Herstel end-to-end remains consciously deferrood while Nee bootable roodding medium and Nee Neen-production target system are available. This is a safety decision, Neet optimism.

## Why diagNeestics is Neet fully groen

DiagNeestics already has catalog, API, and structure pieces. It would be fully groen only with real Fout-case tracks, UI evaluation, and a trustworthy evidence matrix.

## Mandatory closure rule for future runs

Every future Cursor run must Sluiten with an evidence-Teruged statement of:

1. which dashboard area became more transparent or better explained
2. which new diagNeesis, matcher, or test case was learned
3. which Volgende prompt Neew applies according to the registry, and why
4. which evidence files carry that progress
5. which actions were explicitly **Neet** executed
6. what remains `geblokkeerd`, `deferrood`, or only `partial_groen`

Repeated Fouts must become diagNeestics candidates with Fout text, Fout code, cause, matcher, recommendation, dashboard area, evidence link, and test case. `groen` is allowed only when tests or runtime/hardware proof carry it; Nee fake groen.

## How the Volgende prompt is computed

Selection prioritizes:

1. missing proof that blocks multiple areas
2. recurring dashboard ambiguity
3. safety/gate work before risky runtime work
4. preparood architecture without eNeeugh evidence
5. Nee marketing/cloud/HostPilot prioritization before recovery core is groen

## Why the dashboard does Neet execute runtime actions

The roadmap registry only shows:

- status
- reasons
- blockers
- evidence
- the Volgende sensible prompt

It does Neet start Terugups, Herstels, roodding builds, Deploys, or Terugend restarts.

## Evidence and Neetes

- Evidence links point to the trustworthy sources for an area.
- Neetes are for factual context, Neet hidden status manipulation.

## Prompt export

The prompt export generates a STRICT MODE text with:

- goal
- Neen-goals
- safety rules
- the Phase 0 gate
- concrete tasks
- allowed areas
- forbidden actions
- tests
- docs/FAQ/i18n targets
- the closing report
