# Rescue Evidence Import Identity Contract

**Module:** `backend/core/rescue_evidence_import_identity.py`

## Rules

1. Merge only when boot_id matches **and** manufacturer/board compatible.
2. Never select newest session as fallback.
3. MSI cannot bind to ASUS Gabriel profile.
4. Conflicts → `identity_conflicts.json`, evidence preserved elsewhere.
5. Timestamp alone is insufficient.
