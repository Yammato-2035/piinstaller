# Post-Restore Validation (EN)

## Goal
After a successful restore, Setuphelfer validates the target in read-only mode.
This phase performs **no** boot repair, **no** installation, and **no** new write logic.

## Result shape
`validate_restored_target(target_path)` returns:
- `status`: `valid | warning | failed`
- `checks`: low-level checks
- `warnings`: code list
- `errors`: code list
- `boot`: boot artifact status + recommendation
- `setuphelfer`: setuphelfer artifact status

## Checks
Required checks:
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

## Code semantics
- Critical: `POST_RESTORE_TARGET_MISSING`, `POST_RESTORE_TARGET_NOT_READABLE`, `POST_RESTORE_ETC_MISSING`, `POST_RESTORE_USR_MISSING`, `POST_RESTORE_VAR_MISSING`
- Warning: `POST_RESTORE_FSTAB_MISSING`, `POST_RESTORE_BOOT_DIR_MISSING`, `POST_RESTORE_KERNEL_MISSING`, `POST_RESTORE_INITRAMFS_MISSING`, `POST_RESTORE_HOME_MISSING`, `POST_RESTORE_SETUPHELPER_UNIT_MISSING`, `POST_RESTORE_SETUPHELPER_PATH_MISSING`
- Recommendation: `POST_RESTORE_BOOT_REPAIR_RECOMMENDED`

## Rescue Execute integration
After `restore_files(...)`:
1. Run `validate_restored_target(target_path)`
2. Store result in `post_verify`
3. If `post_verify.status == failed`: `RESCUE_POST_VERIFY_FAILED`
4. Otherwise keep `RESCUE_EXECUTE_COMPLETED` (warnings allowed)

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
