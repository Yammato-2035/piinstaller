# Physical retest 2026-07-26 ~10:30 — Hybrid / AMD Safe / Basic Emergency

## Results

| Profile | Observed | Classification |
|---------|----------|----------------|
| Hybrid Auto (AMD display) | Boot to `cups.service` OK, then no console; system appears stuck. eth0 up / internet OK. No network printer involved. | **probable** multi-user/VT dead-console (same class as earlier getty/CUPS hang). CUPS start is a symptom of multi-user, not printer dependency. |
| AMD Safe | Boot to USB HID Core, then black screen; no terminal | **probable** KMS/VT failure without rescue shell pin |
| Basic Emergency | Reached login; `Mint` rejected; empty rejected; then hung | **confirmed** rescue text path works to auth prompt; **operator error** on username case; hang after failed logins possible |

## CUPS note

`Started cups.service` does **not** mean a network printer is required. It is a normal multi-user service. Masking `cups.service` on Rescue profiles removes noise and avoids waiting on printer discovery.

## Login on Rescue / Emergency

At maintenance / sulogin:

1. Prompt like `Give root password for maintenance` → press **Enter** only (empty root password on live).
2. If `login:` appears → username **`root`** (lowercase), password **Enter** (empty).
3. Do **not** type `Mint` (wrong case). Live user is **`mint`** (all lowercase) with empty password — only if you are on a getty, not sulogin.
4. After too many failures, wait or use Ctrl+Alt+F2 / Ctrl+Alt+F9 (debug-shell).

## Fix applied after this retest

- Hybrid Auto + AMD Safe: `systemd.unit=rescue.target` (keep AMD KMS, no nomodeset).
- Mask `cups.service` / `cups-browsed.service` on these profiles.
- Menu titles include `root+Enter` hint.
