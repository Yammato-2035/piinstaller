# Deploy Write Execute Dry-Run

This phase introduces final pre-write contract checks with session+token binding while remaining fully simulation-only.

## Inputs

- validated write plan
- validated image inspect payload
- required confirmation codes

## Output

- stable simulated execution sequence
- no device access side effects
