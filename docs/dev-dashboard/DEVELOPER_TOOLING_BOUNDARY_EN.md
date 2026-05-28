# Developer Dashboard Tooling Boundary (EN)

## Purpose

The Developer Dashboard is an internal development, governance, and evidence tool. It is not a normal end-user Setuphelfer product feature.

## Mandatory Rules

1. The Developer Dashboard is **internal tooling**.
2. It is **not part** of the regular Setuphelfer user interface.
3. It must not be marketed as a product feature.
4. It must not be embedded into normal user flows such as backup, restore, or rescue.
5. It must not provide a **free shell**.
6. It must not execute dangerous actions directly.
7. It may start read-only checks and safe tests only through an allowlist.
8. It may create operator handoffs but must not replace operator actions.
9. Every command run must produce evidence.
10. Roadmap and dashboard statuses must only change based on evidence.

## Explicit Prohibitions

- No free command input
- No interactive terminal emulation
- No `sudo` execution from the dashboard runner
- No `apt install`/`upgrade`, no `dd`, `mkfs`, `parted write`
- No restore/backup/USB-write execution from the Developer Dashboard

## Cursor Execution Rule (mandatory)

Cursor must not announce or start background tasks, auto-efficiency chains, ingest jobs, commit/push chains, or delayed follow-up status runs.  
Each run must end synchronously with a complete final report.  
If operator privileges are required, Cursor may only create an operator handoff and must not start background execution.
