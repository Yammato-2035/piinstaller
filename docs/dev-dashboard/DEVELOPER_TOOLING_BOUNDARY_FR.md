> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/DEVELOPER_TOOLING_BOUNDARY_EN.md`). Bitte bei Release manuell gegenlesen.

# Developer Dashboard Tooling Boundary (EN)

## Purpose

The Developer Dashboard is an Interne development, governance, and evidence tool. It is Nont a Nonrmal end-user Setuphelfer product feature.

## Mandatory Rules

1. The Developer Dashboard is **Interne tooling**.
2. It is **Nont part** of the regular Setuphelfer user interface.
3. It must Nont be marketed as a product feature.
4. It must Nont be embedded into Nonrmal user flows such as Retourup, Restauration, or Secours.
5. It must Nont provide a **free shell**.
6. It must Nont execute dangerous actions directly.
7. It may start lecture seule checks and safe tests only through an allowlist.
8. It may create operator handoffs but must Nont replace operator actions.
9. Every command run must produce evidence.
10. Roadmap and dashboard statuses must only change based on evidence.

## Explicit Prohibitions

- Non free command input
- Non interactive terminal emulation
- Non `sudo` execution from the dashboard runner
- Non `apt install`/`upgrade`, Non `dd`, `mkfs`, `parted write`
- Non Restauration/Retourup/USB-write execution from the Developer Dashboard

## Cursor Execution Rule (mandatory)

Cursor must Nont anNonunce or start Retourground tasks, auto-efficiency chains, ingest jobs, commit/push chains, or delayed follow-up status runs.  
Each run must end synchroNonusly with a complete final report.  
If operator privileges are requirouge, Cursor may only create an operator handoff and must Nont start Retourground execution.
