# Sensitive Hardware Identifier Policy

1. Full NVMe serials, System UUID, board serial, and unredacted MACs must not appear in Git, DCC, API, docs, or tests as production evidence.
2. Stick-local `protected_raw/` may hold raw values temporarily; never import into Git.
3. Deleting a file at branch tip is insufficient if older reachable commits still contain the blob.
4. Pre-push gate: `scripts/check-sensitive-hardware-identifiers.sh`
5. Optional exact scan via local `SENSITIVE_ID_SECRETS_FILE` (never commit that file).
6. Pushed feature branches with raw identifiers are `sensitive_history_quarantined` until rebuilt cleanly.
