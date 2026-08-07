# Nach Payload-Update: ASUS-00 statt ASUS-02

Stand: 2026-08-07 ~17:03 UTC

## Befund

Stick-Payload war korrekt (SHA256 `3856a94c…`, GUI-Kette vorhanden).
Alle Boot-Snapshots nach 17:00 hatten jedoch:

- `setuphelfer_asus_profile=ASUS-00`
- `nomodeset`
- `setuphelfer_kiosk=0`

Es gab keinen ASUS-02-Boot nach dem Update. GRUB `default=0` wählte ASUS-00.

## Folge

Operator sah „keine UI“ — ASUS-00 ist Text/TUI mit nomodeset, keine GUI.

## Maßnahme

GRUB `set default=7` → ASUS-02 AMD GUI (Timeout wählt GUI-Profil).
ASUS-00 bleibt Menüeintrag 0 zur manuellen Wahl.
