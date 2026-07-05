> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/DEVELOPER_TOOLING_BOUNDARY_EN.md`). Bitte bei Release manuell gegenlesen.

# Developer Dashboard Tooling Boundary (EN)

## Purpose

The Developer Dashboard is an Intern development, governance, and evidence tool. It is Neet a Neermal end-user Setuphelfer product feature.

## Mandatory Rules

1. The Developer Dashboard is **Intern tooling**.
2. It is **Neet part** of the regular Setuphelfer user interface.
3. It must Neet be marketed as a product feature.
4. It must Neet be embedded into Neermal user flows such as Terugup, Herstel, or roodding.
5. It must Neet provide a **free shell**.
6. It must Neet execute dangerous actions directly.
7. It may start alleen-lezen checks and safe tests only through an allowlist.
8. It may create operator handoffs but must Neet replace operator actions.
9. Every command run must produce evidence.
10. Roadmap and dashboard statuses must only change based on evidence.

## Explicit Prohibitions

- Nee free command input
- Nee interactive terminal emulation
- Nee `sudo` execution from the dashboard runner
- Nee `apt install`/`upgrade`, Nee `dd`, `mkfs`, `parted write`
- Nee Herstel/Terugup/USB-write execution from the Developer Dashboard

## Cursor Execution Rule (mandatory)

Cursor must Neet anNeeunce or start Terugground tasks, auto-efficiency chains, ingest jobs, commit/push chains, or delayed follow-up status runs.  
Each run must end synchroNeeusly with a complete final report.  
If operator privileges are requirood, Cursor may only create an operator handoff and must Neet start Terugground execution.
