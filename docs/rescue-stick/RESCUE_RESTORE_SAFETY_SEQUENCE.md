# Rescue Restore Safety Sequence

**RS-P1:** Nur Roadmap — kein Execute.

1. Backup erfolgreich
2. Verify erfolgreich
3. Backup-Medium eindeutig
4. Restore-Preview erfolgreich
5. Dry Restore auf Testziel
6. Operator bestätigt Restore-Testziel
7. Echter Restore auf freigegebenes Ziel
8. Bootprüfung
9. Serviceprüfung
10. Systemplatte löschen nur nach Backup + Verify + Preview + zweiter Freigabe

## Harte Blocker

- Kein Restore ohne Verify
- Kein Restore auf Originalquelle
- Kein Löschen ohne vollständige Evidence
- Kein Restore bei fehlendem Manifest/SHA256/Schlüssel
