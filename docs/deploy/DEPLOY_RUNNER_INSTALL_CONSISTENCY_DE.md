# Deploy Runner Install Consistency Audit (read-only)

## Ziel

Konsistenzpruefung zwischen Install-Plan, Install-Validator und Package-Blueprint.

## Pruefbereiche

- Pfadkonsistenz (Runner, Jobdir, Sudoers, Logdir)
- Rechte-/Rollenkonsistenz
- Sudoers-Regelkonsistenz
- Rollback-Code-Abgleich
- Validation-Step-Abgleich

## API

- `POST /api/deploy/runner/install/consistency`
