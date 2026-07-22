# RUNTIME_DEPLOY_PLAN

- profile: `runtime-opt`
- target: `/opt/setuphelfer`
- source_commit: `9e4c487cfd700c7d34e63a2d249e46785689ac67`
- application_version: `1.9.21.2`
- rescue_payload_version (not deployed): `1.10.2.3`
- source_dirty: `True`

## Components
- **backend**: action=`copy_or_install` required=`True`
- **web_frontend**: action=`build` required=`True`
- **tauri**: action=`skip` required=`False` reason=`not_required_for_runtime_opt`
- **rescue_payload**: action=`skip` required=`False`
- **systemd**: action=`install_or_sync` required=`True`
- **deploy_manifest**: action=`generate` required=`True`
