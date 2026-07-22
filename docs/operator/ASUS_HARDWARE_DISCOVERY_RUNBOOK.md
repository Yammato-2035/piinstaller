# Hardware Discovery Runbook (Gabriel / G513QM)

1. Boot GRUB **Setuphelfer ASUS Hardwarediagnose (nur Lesen)**.
2. Confirm text mode: `setuphelfer_mode=text`, `nomodeset`, storage/BIOS/install writes locked.
3. Confirm operator phrase; wait for all TUI phases including SMART, Windows logs, checksums.
4. Do not power off until “Stick kann nach dem Herunterfahren entfernt werden”.
5. Import only the exact boot_id + run_id with `terminal=true` and Completion/Partial marker.
6. Never attach MSI or older nonterminal sessions.
