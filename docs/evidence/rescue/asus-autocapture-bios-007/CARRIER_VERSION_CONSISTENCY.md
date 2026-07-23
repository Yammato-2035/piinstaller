# CARRIER_VERSION_CONSISTENCY

```text
carrier_version_consistency = passed
expected = 1.10.4.0
```

SquashFS carriers (all match):

- `opt/setuphelfer-rescue/VERSION`
- `opt/setuphelfer-rescue/rescue_payload_version` (plaintext — previously stale, now synced)
- `opt/setuphelfer-rescue/config/rescue_payload_version.json`
- `opt/setuphelfer-rescue/config/version.json`

ESP carriers synced to `1.10.4.0` + payload SHA.

Gate module: `backend/core/asus_lab/carrier_consistency.py` + extended `verify_payload_version_carriers`.
