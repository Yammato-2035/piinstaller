# RS-F2B.1 Local Telemetry Final

- **Ampel:** yellow (Dev SETUP_LOGS-Spool OK, MSI-Retest offen)
- **MSI-Boot:** nur `/run/.../telemetry-spool`
- **Fix:** `resolve_rescue_evidence_root()` bevorzugt SETUP_LOGS
- **Redaction:** getestet, `network_upload_attempted=false`
