# FAQ — DCC-VIS-001 (en)

## Why is the DCC red?

Usually: runtime gate (Phase 0) not green, missing developer token, or standalone mode. Red does not always mean the backend is down.

## Why is the API reachable but the runtime gate blocked?

`/api/version` only checks the local backend process. The runtime gate also checks deploy drift, `/opt` state and service status.

## What is the developer token?

Header `X-Setuphelfer-Developer-Token` for dev-dashboard routes. Stored locally in the browser — never in git.

## Why are backup/restore/deploy locked?

The DCC stays read-only while runtime gates are red (hard safety).

## What is the visible changelog?

Completed phases (e.g. TEL-011) with result, workspace and visibility per surface.

## When to switch workspace?

When the next phase lives in another repo (e.g. TEL-012 → telemetry server).

## Why is TEL-011 complete but not green in the DCC?

Completed in the telemetry server; DCC visibility was wired in DCC-VIS-001.
