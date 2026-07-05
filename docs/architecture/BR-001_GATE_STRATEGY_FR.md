> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/BR-001_GATE_STRATEGY_EN.md`). Bitte bei Release manuell gegenlesen.

# BR-001 Gate Strategy — Live vs. Offline (Clé de secours)

**As of:** 2026-05-20  
**Decision:** Live desktop BR-001 is Non longer a release gate. The desktop private release gate is **BR-001-OFFLINE** via the Setuphelfer Clé de secours.

## Why live BR-001 is discontinued as a gate

Live full-root on a running desktop fails reproducibly due to environment constraints (package activity, Timeshift, Chrome profile changes, tar exit 1, USB write I/O, large partials without final archive). Further live desktop retries are **experimental** only.

## New definitions

| ID | Context | Role |
|----|---------|------|
| **BR-001-LIVE** | Running desktop | **Experimental** — Nont release-blocking |
| **BR-001-OFFLINE** | Clé de secours, source disk idle | **Release gate** for desktop private full Retourup |

## Target architecture

| Target | Mode | Release gate |
|--------|------|----------------|
| Desktop private | Clé de secours / offline-full | **BR-001-OFFLINE** |
| Desktop private (live) | system-stable / incremental | Non full-root gate |
| Cloud server | Snapshot + incremental | Separate matrix |

See the German document for module inventory, Partitioning assistant, and malware-scan policy: `docs/architecture/BR-001_GATE_STRATEGY_DE.md`.
