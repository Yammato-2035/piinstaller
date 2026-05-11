# Recovery Activation Controlled Execute (DE)

## Ziel

Diese Phase fuehrt erstmals eng begrenzte Aktivierungsschritte aus, aber nur aus einer gueltigen Activation-Session mit Token, TTL und Plan-Bindung.

## Sicherheitsgrenzen

- Kein Schreiben ausserhalb `target_path`
- Session ist single-use (bei Start sofort verbraucht)
- Steps nur aus `selected_steps` der Session
- Fail-Fast: bei erstem Step-Fehler wird abgebrochen
- Keine Passwortaktivierung
- Kein Root-Login
- Keine Host-Service-Aktivierung
- Keine Windows-/Dualboot-/Unknown-Aktivierung

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

## Umgesetzte Controlled Actions

- `ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH`: schreibt `authorized_keys` unter `target_path/home/setuphelfer-recovery/.ssh/authorized_keys`
- `ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN`: bereitet `PasswordAuthentication no` und `PermitRootLogin no` unter `target_path/etc/ssh/sshd_config.setuphelfer_recovery` vor
- `ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE`: schreibt nur Plan/Marker, erstellt keinen Host-User
- `ACTIVATION_STEP_ENABLE_SSH_SERVICE`: schreibt nur Ziel-Markerdatei
- `ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND`: nutzt nur lokale vorhandene Quellen, sonst Step-Fehler
- `ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE`: standard `127.0.0.1`, `0.0.0.0` nur bei `allow_lan_backend_bind=true` mit Warning
- `ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL`: schreibt nur Plan-Datei
- `ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS`: schreibt Access-Report unter `target_path`

## Nicht Teil dieser Phase

- kein Host-Login-Setup
- kein Host-User-Management
- kein Host-Service-Start
- keine aktive Netzwerk-/Firewall-Aenderung
- kein garantiert sofort erreichbarer Fernzugriff
