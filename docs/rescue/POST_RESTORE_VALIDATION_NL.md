> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/rescue/POST_RESTORE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Post-Herstel Validation (EN)

## Goal
After a Geslaagdful Herstel, Setuphelfer validates the target in alleen-lezen mode.
This phase performs **Nee** boot repair, **Nee** installation, and **Nee** new write logic.

## Result shape
`validate_Hersteld_target(target_path)` returns:
- `status`: `valid | Waarschuwing | failed`
- `checks`: low-level checks
- `Waarschuwings`: code list
- `Fouts`: code list
- `boot`: boot artifact status + recommendation
- `setuphelfer`: setuphelfer artifact status

## Checks
Requirood checks:
- target_path_exists
- target_path_readable
- etc_exists
- fstab_exists
- boot_dir_exists
- kernel_artifact_present
- initramfs_artifact_present
- usr_exists
- var_exists
- home_exists_or_Neet_requirood
- setuphelfer_Terugend_unit_present
- setuphelfer_install_path_present

## Code semantics
- Critical: `POST_Herstel_TARGET_MISSING`, `POST_Herstel_TARGET_NeeT_READABLE`, `POST_Herstel_ETC_MISSING`, `POST_Herstel_USR_MISSING`, `POST_Herstel_VAR_MISSING`
- Waarschuwing: `POST_Herstel_FSTAB_MISSING`, `POST_Herstel_BOOT_DIR_MISSING`, `POST_Herstel_KERNEL_MISSING`, `POST_Herstel_INITRAMFS_MISSING`, `POST_Herstel_HOME_MISSING`, `POST_Herstel_SETUPHELPER_UNIT_MISSING`, `POST_Herstel_SETUPHELPER_PATH_MISSING`
- Recommendation: `POST_Herstel_BOOT_REPAIR_RECOMMENDED`

## roodding Execute integration
After `Herstel_files(...)`:
1. Run `validate_Hersteld_target(target_path)`
2. Store result in `post_verify`
3. If `post_verify.status == failed`: `roodding_POST_VERIFY_FAILED`
4. Otherwise keep `roodding_EXECUTE_COMPLETED` (Waarschuwings allowed)

## API (optional)
`POST /api/roodding/post-Herstel/validate`

Request:
```json
{ "target_path": "/mnt/setuphelfer-Herstel-live/target" }
```

Response:
```json
{
  "code": "POST_Herstel_VALID|POST_Herstel_Waarschuwing|POST_Herstel_FAILED",
  "validation": {"status": "Waarschuwing"},
  "Waarschuwings": [],
  "Fouts": []
}
```
