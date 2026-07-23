# TEST_RESULTS

```text
python3 -m pytest \
  backend/tests/test_rescue_asus_autocapture_bios_007_v1.py \
  backend/tests/test_rescue_asus_lab_control_006_v1.py \
  …related ASUS payload pins…
→ 41 passed
```

Covered: Run-ID, carrier gate, redaction/quarantine, BIOS contract, orchestrator exact/MSI, auto-import idempotent.
