# Fix input audit (1.10.0.60)

| Requirement | Status |
|-------------|--------|
| Runtime root `/run/setuphelfer/tui-input-diagnostics` | present |
| Persistent root via SETUP_LOGS resolver | present |
| Mount wait 60s / 2s | present |
| Safe mount only in finalizer | present |
| `.partial` migration | present |
| Manifest + SHA256 verify | present |
| Atomic publish | present |
| Idempotent finalizer | present |
| Runtime retained on failure | present |
| Shutdown gate | present |
| Import ignores `.partial` | present |
| Auto-shutdown default off | present |
| Payload SoT `1.10.0.60` | present in `config/rescue_payload_version.json` |
