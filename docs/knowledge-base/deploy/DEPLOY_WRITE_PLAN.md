# Deploy Write Plan

Deploy Write Plan is the final dry-run style planning layer before any future write execution phase.

## What it does

- re-validates target and safety signals
- validates inspected image status for write readiness
- returns simulated operations and required confirmations

## What it does not do

- no disk writes
- no partitioning/formatting
- no mount/loop/extract
