# Telemetry Server (private skeleton)

Port **8101**. Implements ingest contract from public `TELEMETRY_SERVER_BETA_0_1.md`.
Forbidden routes: `/execute`, `/command`, `/shell`, `/fix`, `/wipe`, etc.

Run lab: `uvicorn app.main:app --port 8101` from this directory (after `pip install fastapi uvicorn`).
