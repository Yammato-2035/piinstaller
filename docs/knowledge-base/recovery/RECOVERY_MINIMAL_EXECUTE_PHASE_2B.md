# Recovery Minimal Execute Phase 2b

## Summary
Implements controlled single-step recovery preparation with real file operations only inside the target path.

## Safety posture
- strict session/token binding
- fail-fast on first step error
- stop further steps after failure
- session consumed (`used=true`) once execution begins

## Explicitly not performed
- SSH activation
- user creation
- network changes
- service enable/start
