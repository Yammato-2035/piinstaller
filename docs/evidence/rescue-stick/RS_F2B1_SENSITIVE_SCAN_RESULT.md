# RS-F2B.1 Sensitive Scan Result

## Geänderte Dateien (staged)

- Treffer `password`/`secret`: nur API-Parameter-Namen, Redaction-Contract, `secrets_exposed: false` Flags — **erlaubt**
- Treffer MAC/IP in Tests: Testvektoren `aa:bb:cc:dd:ee:ff`, `192.168.1.50` — **erlaubt**
- `RS_F2B1_REBUILD_RESULT.json`: Pfad auf relativ korrigiert vor Commit
- `setuphelfer-rescue-common.sh`: Lab-IP nicht Teil des Diffs (pre-existing default)

## Blockierend

Keine echten Secrets, WLAN-Passwörter oder Cloud-Credentials in staged Files.

## Ergebnis

`ok` — Commit erlaubt.
