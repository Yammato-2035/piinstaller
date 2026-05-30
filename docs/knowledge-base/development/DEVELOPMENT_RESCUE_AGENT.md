# Development Rescue Agent

Read-only local collector + HTTP client for Development Server ingest.

- Module: `backend/devserver_agent/`
- Spool: `docs/evidence/runtime-results/dev-agent-spool/`
- systemd template: `packaging/systemd/setuphelfer-dev-agent.service` (default disabled)

Public rescue never auto-uploads. Local lab sends to `127.0.0.1` only in MVP.
