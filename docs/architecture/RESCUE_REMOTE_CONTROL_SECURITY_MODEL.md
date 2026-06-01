# Rescue Remote Control — Security Model (Phase 1)

## Pflichtentscheidungen

1. **Keine freie Remote-Shell** als Standard.
2. Ausführung nur über **allowlisted Runbooks**.
3. Runbooks sind explizit registriert (`ALLOWLISTED_RUNBOOKS` im Backend).
4. Jedes Runbook: `runbook_id`, `description`, `allowed_mode`, `requires_operator_consent`, `dangerous`, `timeout_seconds`, Redaction.
5. Phase 1: nur `read_only` und `diagnostic`.
6. `controlled_write` ist **deaktiviert**.
7. Agent **pullt** Jobs vom lokalen Development Server (HTTPS, local_lab).
8. Server scannt **nicht** das LAN.
9. Verboten in Phase 1: `dd`, `mkfs`, `mount`, `umount`, `parted`, `wipefs`, `rm -rf`, `apt install`, `apt upgrade`.
10. Erlaubt: `journalctl`, `dmesg`, `lsblk`, `findmnt`, `ip`, `nmcli`, definierte Setuphelfer-Logs, Connectivity-Test.
11. Outputs werden **redigiert**.
12. Keine Tokens/Keys/Passwörter in API-Responses oder Evidence.

## Warum keine freie Remote-Shell?

Der Rettungsstick läuft in einer potenziell sensiblen Datenrettungsumgebung. Eine interaktive Shell vom Development Server aus erhöht Missbrauchs- und Fehlbedienungsrisiko, ist schwer auditierbar und widerspricht dem Prinzip „nur definierte Diagnose-Schritte“. Runbooks sind reproduzierbar, testbar und liefern strukturierte Evidence.

## Pairing

- Einmaliger Pairing-Token (nicht im Repo).
- Server speichert nur `pairing_token_hint` (maskiert).
- Session endet nach Reboot (Live-System).

## Modi

| Modus | Phase 1 |
|-------|---------|
| `local_lab` | erlaubt |
| `rescue_user` | später |
| `school` / `production` | blockiert |
