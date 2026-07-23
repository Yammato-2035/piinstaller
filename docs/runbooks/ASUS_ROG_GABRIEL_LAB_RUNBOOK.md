# ASUS ROG Gabriel Lab Runbook

1. Confirm stick payload SHA matches `1.10.3.0` / manifest.
2. Boot ASUS Hardwarediagnose or WinPE with `SETUPHELFER_WIN_DIAG`.
3. Export `SETUPHELFER_WIN11_RUN_ID` from prepare API or generator.
4. Start live capture before Windows Setup.
5. After hang/finish: import by Run-ID only; evaluate heartbeats + file counts.
6. BitLocker: status only — no mutation.
7. BIOS 335 / Mint: only after Live-Evidence decision docs.
