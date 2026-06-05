# KB — BitLocker Read-Only Policy

## Regeln

1. BitLocker erkannt → Status dokumentieren (`WIN-BITLOCKER-001`).
2. Partition gesperrt ohne Recovery Key → **keine** verwertbare Datei-/Registry-Analyse (`WIN-BITLOCKER-002`).
3. Recovery Key **niemals** im Repo, Evidence oder Dashboard persistieren.
4. Kein brutales Mount, kein `manage-bde` Unlock aus Agent-Kontext.

## Operator-Handoff

Operator liefert Recovery Key lokal; Stick mountet danach read-only mit dokumentiertem Mount-Plan.
