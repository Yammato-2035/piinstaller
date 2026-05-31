# Rescue Dev Agent — QEMU Server URL Analysis

**Date:** 2026-05-31
**HEAD:** 7118c69 (pre-fix)

## Current URL resolver (before fix)

- Source: `SETUPHELFER_DEV_AGENT_SERVER_URL` in env/profile
- Default: `http://127.0.0.1:8000` (`backend/devserver_agent/config.py`)
- CLI `--server` overrides env at runtime
- `validate_server_url()` allows private/loopback hosts including `10.0.2.2`
- No QEMU fallback chain; no health probing across candidates

## Root cause (QEMU smoke)

Guest `127.0.0.1:8000` → guest loopback, not host Dev Server → connection refused (expected).

## Target behavior

- Explicit `developer-qemu` profile with `http://10.0.2.2:8000`
- Resolver probes candidates; selects first reachable for `local_lab`
- Spool when all fail; never open public upload

## Security boundaries

- Public profile unchanged (disabled, no auto-upload)
- No tokens in logs
- No SSH enable by default
- Remote console local bind only
