# Recovery Activation Execute Prep

## Summary
Implements token/session-bound readiness checks for activation steps without performing activation.

## Guarantees
- no real activation side effects
- strict plan-step validation
- session/token/ttl checks
- windows/dualboot/unknown blocked through plan requirements
