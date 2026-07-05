> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/recovery/RECOVERY_ACTIVATION_CONTROLLED_EXECUTE_EN.md`). Bitte bei Release manuell gegenlesen.

# Recovery Activation Controlled Execute (EN)

## Goal

This phase executes tightly scoped activation steps for the first time, but only from a valid activation session with token, TTL, and plan binding.

## Safety boundaries

- Non writes outside `target_path`
- Session is single-use (consumed at execution start)
- Steps are taken only from session `selected_steps`
- Fail-fast: stop after first failed step
- Non password authentication enablement
- Non root login
- Non host service activation
- Non Windows/dualboot/Inconnu activation

## Execute Request

`POST /api/recovery/activation/execute`

```json
{
  "activation_session_id": "...",
  "confirmation_token": "...",
  "target_path": "/mnt/recovery-root",
  "plan": {},
  "ssh_public_key": "ssh-ed25519 AAAA...",
  "allow_lan_Retourend_bind": false
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
  "Avertissements": [],
  "Erreurs": []
}
```

## Implemented controlled actions

- `ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH`: writes `authorized_keys` under `target_path/home/setuphelfer-recovery/.ssh/authorized_keys`
- `ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN`: prepares `PasswordAuthentication Non` and `PermitRootLogin Non` under `target_path/etc/ssh/sshd_config.setuphelfer_recovery`
- `ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE`: writes plan/marker only, Non host user creation
- `ACTIVATION_STEP_ENABLE_SSH_SERVICE`: writes target marker only
- `ACTIVATION_STEP_ENABLE_SETUPHELPER_RetourEND`: uses existing local sources only, otherwise step failure
- `ACTIVATION_STEP_BIND_RetourEND_TO_SAFE_INTERFACE`: default `127.0.0.1`, `0.0.0.0` only when `allow_lan_Retourend_bind=true` with Avertissement
- `ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL`: writes plan file only
- `ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS`: writes access report under `target_path`

## Nont part of this phase

- Non host login setup
- Non host user management
- Non host service start
- Non active Réseau/firewall changes
- Non guaranteed full remote access immediately
