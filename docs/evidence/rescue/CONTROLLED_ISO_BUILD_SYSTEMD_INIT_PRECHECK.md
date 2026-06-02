# Controlled ISO Build — systemd-init Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Bootappend (config/binary)

```
LB_BOOTAPPEND_LIVE="boot=live components init=/lib/systemd/systemd ... setuphelfer_rescue=1 hostname=setuphelfer-rescue username=user keyboard-layouts=de locales=de_DE.UTF-8 timezone=Europe/Berlin"
```

## Integration

| Thema | Status |
|-------|--------|
| systemd als PID 1 | **init=/lib/systemd/systemd** in Live-Bootappend |
| Setuphelfer Rescue Runtime | Hooks + `setuphelfer.list.chroot`, Temp-Runtime-Bundle |
| Live user/keyboard/locale | **user**, **de**, **de_DE.UTF-8**, **Europe/Berlin** |
| Backend local-only | dokumentiert in Runbook / `start-backend-localonly.sh` |

## Hooks

`config/hooks/005-setuphelfer-live-user.chroot` — Kommentar zu init=/systemd und Login user/live.

## VM-Historie

Runbook `validate-rescue-iso-squashfs.sh` Exit 15/16 für fehlendes systemd-init — Precheck-Config **adressiert**.
