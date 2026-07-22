# Release Notes — PI-RS-ASUS-WIN11-RETEST-005

## Payload 1.10.2.3

- Expanded `SETUPHELFER_WIN_DIAG` collector (cmd + ps1 + boot info)
- Controlled retest module: role binding, Linux NVMe isolation, Stage A/B gates, BIOS causality
- API routes under `/win11-retest/*`
- DCC block for Win11 retest (no fake-green on installer start)
- i18n de/en/fr/nl (stick + frontend)
- Docs: architecture contracts, operator runbooks, FAQ, KB
- App version unchanged: **1.9.21.2**
- Endstatus: **ready_for_windows_retest_bios331** (physical Stage A not run in this commit)
