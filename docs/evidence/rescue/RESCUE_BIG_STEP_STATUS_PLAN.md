# Rescue Big Step — Status Plan

**Datum:** 2026-05-24
**Git HEAD:** `83ec644` (tar/adduser retry)
**real_iso_build_allowed:** `false`
**usb_write_allowed:** `false`

| Bereich | Ziel | Status | Blocker |
|---------|------|--------|---------|
| auto/config noauto | Fix | **green** | — |
| Clean build state | chroot leer | **green** | rm ohne sudo ok |
| Temp/Tree Validator | Exit 0 | **green** | — |
| Controlled ISO Build | ISO | **review_required** | sudo lb build Operator |
| Rescue ISO artifact | SHA256 | **blocked** | — |
| USB Write | blockiert | **blocked** | — |

## Entscheidung

1. **tar/adduser:** verunreinigter chroot aus fakeroot + cache — **kein ext4-Problem**.
2. **Fix:** Clean + `auto/config noauto` — Build-State bereit.
3. **Nächster Schritt:** Operator `sudo lb build noauto` im Terminal.
