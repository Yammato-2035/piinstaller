# 11 – Repair Path: **E**

Kein Code-Fix. Nächster physischer Lauf:

1. GRUB: TUI-Eingabediagnose (wie diesmal).
2. Auf tty2 Assistenten **vollständig** durchlaufen (Tasten, Fragen, Finalize).
3. Shutdown-Frage mit **J** erst nach „Evidence finalisiert“.
4. Prüfen: auf Stick existiert `SETUP_LOGS/tui-input-diagnostics/<RUN_ID>/` mit `SHA256SUMS`.
5. Erst dann Import.

Optional später (separater Auftrag): Evidence periodisch/flush bei Abbruch persistieren — **nicht** in diesem Auftrag.
