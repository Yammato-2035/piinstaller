# Deploy Write Test Harness

The test harness enables controlled byte-limited copy tests to approved regular files only.

## Inputs

- final confirmation result
- validated image inspect payload
- approved test target path

## Guarantees

- no real blockdevice writes
- strict path and file-type checks
- single-use session and TTL
