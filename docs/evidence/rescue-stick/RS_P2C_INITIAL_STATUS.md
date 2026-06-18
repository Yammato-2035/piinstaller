# RS-P2C Initial Status

| Feld | Wert |
|------|------|
| Branch | main |
| HEAD (Start) | 3390fd7 |
| Version (Start) | 1.9.5.1 |
| Version (Ziel) | 1.9.5.2 |
| Public/Private-Gate | 0 (ok) |
| Module-Boundary-Gate | 0 (review_required warnings) |
| Runtime-Drift | erwartet (/opt 1.9.2.0, Gate Exit 20) |
| RS-P2A Squashfs SHA256 | b8619ca61774baade694ae7569484b61053c45c0da2b380d2ea9235aea2e4275 |

## MSI-Boot-Befund (1.9.5.1)

| Signal | Wert |
|--------|------|
| grub_background_visible | true |
| grub_text_menu_visible | partial_bad |
| grub_buttons_visible | false |
| rescue_gui_visible | false |
| black_screen_after_rescue_start | true |
| cursor_blinking | true |
| user_prompt_visible | false |
| backup_plan_created | false |

## Execute-Policy

| Aktion | Erlaubt |
|--------|---------|
| backup_execute | false |
| restore_execute | false |
| wipe | false |
