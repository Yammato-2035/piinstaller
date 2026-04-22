# Backup-Ziel: Rechte ohne manuelles chown pro Lauf

## Kurzfassung

- **Problem:** Externe Medien sind oft als `root:root` mit `0755` gemountet; der Setuphelfer-Backend-Prozess schreibt nicht als root.
- **Lösung:** Gruppe **`setuphelfer`**, Mount-Punkt **`root:setuphelfer`**, Modus **`0770`**, Backend-Unit mit **`SupplementaryGroups=setuphelfer`** (siehe `setuphelfer-backend.service` und `scripts/install-system.sh`).
- **Prüfung:** Vor dem Packen führt `validate_backup_target` einen echten Schreibtest aus; bei Fehlschlag: Schlüssel `backup_recovery.error.backup_target_not_writable` (kein automatisches `chown` im Normalbetrieb).
- **Nur Tests/VM:** `SETUPHELFER_FIX_PERMISSIONS=1` oder `tools/vm-test/scripts/in-guest-prepare-backup-disk.sh` mit `VMTEST_BACKUP_OWNER_GROUP`.

**Vollständige Referenz:** [../developer/BACKUP_RECOVERY_ENGINES.md](../developer/BACKUP_RECOVERY_ENGINES.md) (Abschnitt „Backup Target Permissions“).

---

## English summary

External disks are often mounted `root:root` `0755`; the backend runs non-root. Use group **`setuphelfer`**, mount point **`root:setuphelfer`** mode **`0770`**, and **`SupplementaryGroups=setuphelfer`** on `setuphelfer-backend`. `validate_backup_target` performs a real write probe; on failure the stable key is `backup_recovery.error.backup_target_not_writable`. For labs only: `SETUPHELFER_FIX_PERMISSIONS=1` or VM helper scripts.
