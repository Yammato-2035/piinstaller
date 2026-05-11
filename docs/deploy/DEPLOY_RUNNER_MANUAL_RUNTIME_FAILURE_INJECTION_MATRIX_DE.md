# Manual Runtime Failure Injection Matrix

Kontrollierte, reversible Failure-Injection-Matrix fuer reale Laptop-Testhardware.

- Nur Testmedien (USB/NVMe/VM), keine produktiven Systempartitionen
- Keine automatische Reparatur, keine automatische Freigabe, keine automatische Ingestion
- `destructive` ist fuer alle Cases erzwungen `false`

API: `POST /api/deploy/runner/manual-runtime/failure-injection-matrix`
