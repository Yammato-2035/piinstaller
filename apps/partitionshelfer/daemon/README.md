# daemon/

Reserviert für Phase 2: privilegierte Ausführung (z. B. `parted`, `mkfs`) mit Policy-Checks und Audit-Log – getrennt von der tkinter-UI.

Schreibpfade müssen mit Setuphelfer `validate_write_target()` und `DEPLOY_WRITE_RUNNER_CONTRACT` abgestimmt werden.
