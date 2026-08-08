# OPERATOR CONFIRMATION 2 — erwartet nach Identity Re-Read

Nach Bestätigung 1 wird das Ziel neu eingelesen. Erst danach:

```text
JA, SETUPHELFER-CARRIER SERIAL 24111412110212 /
FINGERPRINT ce2e34b7f5ea4e41
AUF PAYLOAD 1.10.6.0 AKTUALISIEREN.
```

Zusätzlich für den offiziellen Writer (Script-Gate):

```text
UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD
```

Und für GRUB/HIGHINFO-Default (separater offizieller Pfad):

```text
UPDATE SETUPHELFER FAT32 ESP GRUB BRANDING
```

`USB_WRITE_ALLOWED=true` nur nach Confirmation 2 + Identity Match.
`NVME_WRITE_ALLOWED` bleibt **false**.
