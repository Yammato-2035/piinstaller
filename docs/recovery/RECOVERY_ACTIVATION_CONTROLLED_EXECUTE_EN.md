# Recovery Activation Controlled Execute (EN)

## Goal

This phase executes tightly scoped activation steps for the first time, but only from a valid activation session with token, TTL, and plan binding.

## Safety boundaries

- No writes outside `target_path`
- Session is single-use (consumed at execution start)
- Steps are taken only from session `selected_steps`
- Fail-fast: stop after first failed step
- No password authentication enablement
- No root login
- No host service activation
- No Windows/dualboot/unknown activation

## Execute Request

`POST /api/recovery/activation/execute`

```json
{
  "activation_session_id": "...",
  "confirmation_token": "...",
  "target_path": "/mnt/recovery-root",
  "plan": {},
  "ssh_public_key": "ssh-ed25519 AAAA...",
  "allow_lan_backend_bind": false
}
```

## Execute Response

```json
{
  "code": "RECOVERY_ACTIVATION_EXECUTE_COMPLETED",
  "activation_session_id": "...",
  "steps": [
    {
      "code": "ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN",
      "status": "completed",
      "result_code": "RECOVERY_ACTIVATION_PASSWORD_LOGIN_DISABLED",
      "details": {}
    }
  ],
  "warnings": [],
  "errors": []
}
```

## Implemented controlled actions

- `ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH`: writes `authorized_keys` under `target_path/home/setuphelfer-recovery/.ssh/authorized_keys`
- `ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN`: prepares `PasswordAuthentication no` and `PermitRootLogin no` under `target_path/etc/ssh/sshd_config.setuphelfer_recovery`
- `ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE`: writes plan/marker only, no host user creation
- `ACTIVATION_STEP_ENABLE_SSH_SERVICE`: writes target marker only
- `ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND`: uses existing local sources only, otherwise step failure
- `ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE`: default `127.0.0.1`, `0.0.0.0` only when `allow_lan_backend_bind=true` with warning
- `ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL`: writes plan file only
- `ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS`: writes access report under `target_path`

## Not part of this phase

- no host login setup
- no host user management
- no host service start
- no active network/firewall changes
- no guaranteed full remote access immediately
