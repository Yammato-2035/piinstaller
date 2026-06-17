# Rescue Backup Encryption Policy

**Stand:** 2026-06-17 · RS-P1 Contract only

## Modi

| Modus | Status |
|-------|--------|
| age | geplant (empfohlen) |
| gpg | optional |
| passphrase_later | Preflight deferred |
| no_encryption_for_lab_only | Operator-Bestätigung |

## Regeln

- Echte Nutzerbackups: Verschlüsselung empfohlen/pflichtnah vor Execute
- Keine Passphrase/Keys in Logs oder Evidence
- `execute_allowed=false` solange Key fehlt (RS-P1)
- Lab-Backup unverschlüsselt nur mit expliziter Operator-Freigabe
