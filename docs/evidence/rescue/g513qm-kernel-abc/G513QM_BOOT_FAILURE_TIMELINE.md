# G513QM boot failure timeline (consolidated)

Sources: hybrid-rebuild Abschlussbericht, physical retest notes, FAILURE_MATRIX, operator reports. Values marked `unknown` / `not_captured` when no artifact exists.

| Lauf | Payload | Kernel | Profil | AMD-KMS | NVIDIA | Ziel erreicht | Freeze-Zeitpunkt | VT erreichbar | Netz erreichbar | Evidence |
|------|---------|--------|--------|---------|--------|---------------|------------------|---------------|-----------------|----------|
| Mint logo hang | mint-live casper | 6.14.0-29 | quiet splash | unknown | unknown | no | Plymouth logo | no | unknown | MINT_LOGO_HANG_FIX_* |
| HID hang | mint-live | 6.14.0-29 | casper no live-media pin | off (later nomodeset) | blacklisted | no | after ASUS M-Key HID | no | unknown | MINT_CASPER_HANG_AFTER_HID_* |
| getty/CUPS dead console | mint-live | 6.14.0-29 | multi-user+nomodeset | off | blacklisted | getty OK text dead | after cups | no | unknown | MINT_DEAD_CONSOLE_* |
| Rescue+nomodeset OK console | mint-live | 6.14.0-29 | rescue.target+nomodeset | off | blacklisted | text console | n/a | yes | unknown | GABRIEL_RESCUE_WORKS_* |
| ubiquity black | mint-live | 6.14.0-29 | startx/openvt under nomodeset | off | n/a | no installer | after startx | no | unknown | BLACK_SCREEN_INVOCATION_* |
| Hybrid Auto → cups | mint-live | 6.14.0-29 | hybrid (no rescue) | on | allow | freeze | after cups.service | no | eth0 up (operator) | PHYSICAL_RETEST_CUPS_HID_* |
| AMD Safe → HID | mint-live | 6.14.0-29 | amd_safe | on | off | freeze | USB HID Core | no | unknown | PHYSICAL_RETEST_CUPS_HID_* |
| Basic Emergency login prompt | mint-live | 6.14.0-29 | basic_emergency | off | off | login prompt | n/a (auth failed Mint) | yes briefly | unknown | PHYSICAL_RETEST_CUPS_HID_* |
| Black before login | mint-live | 6.14.0-29 | hybrid default / KMS | on | — | no | before login input | no | unknown | PHYSICAL_RETEST_BLACK_BEFORE_LOGIN.md |
| Control A official 6.8 | — | — | — | — | — | not_tested | — | — | — | pending |
| Control B official 22.3 | — | — | — | — | — | not_tested | — | — | — | pending |
| Control C KMS capture | — | — | — | — | — | not_tested | — | — | — | pending |

## Working hypothesis (not confirmed)

1. `nomodeset` text path can reach a prompt; AMD-KMS paths freeze early.
2. Blind `startx`/`openvt` under nomodeset was a Setuphelfer handoff fault (separate).
3. Distinguishing Setuphelfer vs kernel 6.14 vs BIOS/HW requires Controls A/B/C (this phase).
