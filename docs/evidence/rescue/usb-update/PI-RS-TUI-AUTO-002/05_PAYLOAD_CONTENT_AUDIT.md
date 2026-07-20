# 05 – Payload Content Audit

| Prüfung | Ergebnis |
|---------|----------|
| VERSION | 1.10.0.59 |
| rescue_payload_version.json | 1.10.0.59 |
| version.json | 1.10.0.59 |
| Diagnosemodul | vorhanden |
| CLI `/usr/local/sbin/setuphelfer-rescue-tui-input-diagnostic` | vorhanden, **+x** |
| Unit | ConditionKernelCommandLine, TTYPath=/dev/tty2, Restart=no |
| Wants-Symlink | relativ `../setuphelfer-rescue-tui-input-diagnostic.service` |
| TUI-Guard | aktiv bei Diag-Flag |
| Python-Import Contract | OK |
| Auto-Start ohne Kernelparameter | nein (ConditionKernelCommandLine) |
