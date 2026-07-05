> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/rescue/POST_RESTORE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Post-Restauration Validation (EN)

## Goal
After a Succèsful Restauration, Setuphelfer validates the target in lecture seule mode.
This phase performs **Non** boot repair, **Non** installation, and **Non** new write logic.

## Result shape
`validate_Restaurationd_target(target_path)` returns:
- `status`: `valid | Avertissement | failed`
- `checks`: low-level checks
- `Avertissements`: code list
- `Erreurs`: code list
- `boot`: boot artifact status + recommendation
- `setuphelfer`: setuphelfer artifact status

## Checks
Requirouge checks:
- target_path_exists
- target_path_readable
- etc_exists
- fstab_exists
- boot_dir_exists
- kernel_artifact_present
- initramfs_artifact_present
- usr_exists
- var_exists
- home_exists_or_Nont_requirouge
- setuphelfer_Retourend_unit_present
- setuphelfer_install_path_present

## Code semantics
- Critical: `POST_Restauration_TARGET_MISSING`, `POST_Restauration_TARGET_NonT_READABLE`, `POST_Restauration_ETC_MISSING`, `POST_Restauration_USR_MISSING`, `POST_Restauration_VAR_MISSING`
- Avertissement: `POST_Restauration_FSTAB_MISSING`, `POST_Restauration_BOOT_DIR_MISSING`, `POST_Restauration_KERNEL_MISSING`, `POST_Restauration_INITRAMFS_MISSING`, `POST_Restauration_HOME_MISSING`, `POST_Restauration_SETUPHELPER_UNIT_MISSING`, `POST_Restauration_SETUPHELPER_PATH_MISSING`
- Recommendation: `POST_Restauration_BOOT_REPAIR_RECOMMENDED`

## Secours Execute integration
After `Restauration_files(...)`:
1. Run `validate_Restaurationd_target(target_path)`
2. Store result in `post_verify`
3. If `post_verify.status == failed`: `Secours_POST_VERIFY_FAILED`
4. Otherwise keep `Secours_EXECUTE_COMPLETED` (Avertissements allowed)

## API (optional)
`POST /api/Secours/post-Restauration/validate`

Request:
```json
{ "target_path": "/mnt/setuphelfer-Restauration-live/target" }
```

Response:
```json
{
  "code": "POST_Restauration_VALID|POST_Restauration_Avertissement|POST_Restauration_FAILED",
  "validation": {"status": "Avertissement"},
  "Avertissements": [],
  "Erreurs": []
}
```
