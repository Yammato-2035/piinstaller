# WINDOWS_LINUX_INSTALL_ORDER_CONTRACT

1. Bind Gabriel machine identity.
2. Bind Windows vs Linux NVMe by stable identity.
3. Isolate Linux NVMe for Windows Setup.
4. Complete controlled Windows 11 install + postcheck.
5. Only then set `linux_install_gate = ready_for_planning`.
6. No Linux write in PI-RS-ASUS-WIN11-RETEST-005.

Windows EFI must land on the Windows NVMe. Linux NVMe must remain unchanged through the Windows phase.
