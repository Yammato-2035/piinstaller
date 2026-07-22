# FAQ PI-RS-ASUS-CAPTURE-FINALIZE-004 (EN)

1. **Why is there no GUI in ASUS hardware diagnosis?** Text profile (`setuphelfer_mode=text`, `skip_gui`). GUI status: `not_applicable_for_text_hardware_discovery` — not a failure.
2. **Why is `nomodeset` active?** Without it, amdgpu created a dummy device on G513QM and the panel stayed black. Remains required for this profile.
3. **What is a terminal diagnosis state?** Exactly one of `complete|partial|failed|cancelled` with `terminal=true`. `running` must not remain after controlled finish.
4. **When may the stick be removed?** Only after the completion message and Completion/Partial marker (after shutdown).
5. **What if no Panther logs are found?** `windows_setup_logs=not_found` (not `failed`) → typically a controlled retest with log collection.
6. **Why do full serials stay only on the stick?** Raw values only in local `protected_raw`; Git/DCC/docs use hashes/masks.
7. **Why is deleting a file in the tip commit not enough?** Older reachable commits still hold blobs — history must be rewritten or rebuilt.
8. **What does `diagnosis_incomplete` mean?** Non-terminal capture or missing required areas (e.g. SMART/finalizer).
