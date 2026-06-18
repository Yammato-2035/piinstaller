# RS-P2A Rescue GUI Failure Analysis

**Root Cause:** Grafische GUI war opt-in (`setuphelfer_kiosk=1` / `ConditionKernelCommandLine`). Standardpfad war Whiptail-TUI. `setuphelfer-rescue-ui.service` startete nicht ohne Kernel-Parameter.

**Fix:** `setuphelfer-rescue-gui-start.sh` + `setuphelfer-rescue-backend-start.sh`; Start-Assistent versucht GUI zuerst, TUI nur mit Fehlermeldung.
