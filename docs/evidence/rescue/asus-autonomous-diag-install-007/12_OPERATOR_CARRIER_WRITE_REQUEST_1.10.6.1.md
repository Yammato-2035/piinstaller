# Carrier Write Request — Payload 1.10.6.1

Status: **`ready_for_carrier_write`** — awaiting dual confirmation.

```text
============================================================
DESTRUKTIVE AKTION – USB-CARRIER UPDATE
============================================================
Zielgerät:        /dev/sda
Modell:           Intenso Ultra Line
Seriennummer:     24111412110212
Fingerprint:      ce2e34b7f5ea4e41
Kapazität:        63333990400 bytes (~58.98 GiB)
Transport:        usb (removable)
Aktueller Payload: 1.10.6.0
Neuer Payload:     1.10.6.1
SquashFS SHA256:   9189c1407afc981e8fa99195a2e30688dc1a9313a3af6cb4df9176f8035a227e
Interne NVMe betroffen: NEIN
============================================================
```

## Bestätigung 1 (wörtlich)

```text
Ich bestätige das identifizierte USB-Zielgerät.
```

## Bestätigung 2 (wörtlich)

```text
Ich bestätige, dass der USB-Stick überschrieben werden darf.
```

Nach beiden: Payload + GRUB HIGHINFO Update via offizielle Scripts, dann Readback.
`NVME_WRITE_ALLOWED` bleibt **false**.
