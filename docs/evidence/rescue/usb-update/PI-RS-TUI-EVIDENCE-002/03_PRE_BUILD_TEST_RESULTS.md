# Pre-build tests

```
PYTHONPATH=backend python3 -m pytest \
  backend/tests/test_rescue_tui_input_diagnostic_v1.py \
  backend/tests/test_rescue_tui_input_evidence_persistence_v1.py -q
→ 65 passed
```

- Existing diagnostic tests: 38
- Persistence tests: 27
- Build worktree: `/home/volker/piinstaller-build-tui-evidence-002` @ `6e96b7a4`
