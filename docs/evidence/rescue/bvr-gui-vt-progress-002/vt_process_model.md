# VT Process Model (target)

```
tty1 (TUI owner)
  setuphelfer-rescue-auto-e2e-tui-display / start-assistant
       |
       |  watchdog starts
       v
VT7 (GUI owner, configurable SETUPHELFER_RESCUE_KIOSK_VT)
  openvt -f -w -c 7 -- setuphelfer-rescue-kiosk-start
    -> Xorg :0 vt7
    -> ui-http-server :8765
    -> chromium --app=.../auto-e2e-progress.html
  after X ready: chvt 7
  on failure/timeout: stop own process group, chvt 1, TUI continues
  on BVR complete: stop chromium/Xorg/wrapper, confirm VT release, then shutdown
```

Rules: never steal TUI VT; never kill foreign processes; visibility = X ready + chromium matching kiosk URL + expected VT active.
