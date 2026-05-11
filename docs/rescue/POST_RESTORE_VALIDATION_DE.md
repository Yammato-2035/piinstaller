# Post-Restore Validation (DE)

## Ziel
Nach einem erfolgreichen Restore wird das Restore-Ziel rein lesend validiert.
Es erfolgt **keine** Boot-Reparatur, **keine** Installation und **keine** neue Schreiblogik.

## Ergebnisstruktur
`validate_restored_target(target_path)` liefert:
- `status`: `valid | warning | failed`
- `checks`: technische Einzelchecks
- `warnings`: Code-Liste
- `errors`: Code-Liste
- `boot`: Boot-Artefakt-Status + Empfehlung
- `setuphelfer`: Setuphelfer-Artefakt-Status

## Checks
Pflichtchecks:
- target_path_exists
- target_path_readable
- etc_exists
- fstab_exists
- boot_dir_exists
- kernel_artifact_present
- initramfs_artifact_present
- usr_exists
- var_exists
- home_exists_or_not_required
- setuphelfer_backend_unit_present
- setuphelfer_install_path_present

## Code-Semantik
- Kritisch: `POST_RESTORE_TARGET_MISSING`, `POST_RESTORE_TARGET_NOT_READABLE`, `POST_RESTORE_ETC_MISSING`, `POST_RESTORE_USR_MISSING`, `POST_RESTORE_VAR_MISSING`
- Warnung: `POST_RESTORE_FSTAB_MISSING`, `POST_RESTORE_BOOT_DIR_MISSING`, `POST_RESTORE_KERNEL_MISSING`, `POST_RESTORE_INITRAMFS_MISSING`, `POST_RESTORE_HOME_MISSING`, `POST_RESTORE_SETUPHELPER_UNIT_MISSING`, `POST_RESTORE_SETUPHELPER_PATH_MISSING`
- Empfehlung: `POST_RESTORE_BOOT_REPAIR_RECOMMENDED`

## Integration in Rescue Execute
Nach `restore_files(...)`:
1. `validate_restored_target(target_path)`
2. Ergebnis unter `post_verify`
3. Bei `post_verify.status == failed`: `RESCUE_POST_VERIFY_FAILED`
4. Sonst bleibt `RESCUE_EXECUTE_COMPLETED` (Warnungen möglich)

## API (optional)
`POST /api/rescue/post-restore/validate`

Request:
```json
{ "target_path": "/mnt/setuphelfer-restore-live/target" }
```

Response:
```json
{
  "code": "POST_RESTORE_VALID|POST_RESTORE_WARNING|POST_RESTORE_FAILED",
  "validation": {"status": "warning"},
  "warnings": [],
  "errors": []
}
```
