# Test results

```
PYTHONPATH=backend python3 -m pytest \
  backend/tests/test_rescue_tui_input_evidence_persistence_v1.py \
  backend/tests/test_rescue_tui_input_diagnostic_v1.py -q
```

Result: **65 passed**

- Existing diagnostic tests: 38 (all green; includes version bump asserts)
- New persistence tests: 27
- `bash -n scripts/rescue/import-tui-input-diagnostic-runs.sh` OK
- Runtime deploy gate: not claimed (no deploy in this task)
